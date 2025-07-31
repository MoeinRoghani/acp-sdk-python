"""
ACP Webhooks Support

Provides webhook-based push notifications and event delivery for ACP agents.
Supports webhook registration, delivery, retry logic, and verification.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from urllib.parse import urlparse

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from ..models.generated import TaskNotificationParams, StreamChunkParams
from ..core.json_rpc import JsonRpcError, JsonRpcProcessor
from ..exceptions import ValidationError


logger = logging.getLogger(__name__)


class WebhookStatus(Enum):
    """Webhook delivery status"""
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    EXPIRED = "EXPIRED"


class EventType(Enum):
    """Types of webhook events"""
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    STREAM_STARTED = "stream.started"
    STREAM_MESSAGE = "stream.message"
    STREAM_ENDED = "stream.ended"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    AGENT_STATUS = "agent.status"
    CUSTOM = "custom"


@dataclass
class WebhookEndpoint:
    """Configuration for a webhook endpoint"""
    id: str
    url: str
    events: List[EventType]
    secret: Optional[str] = None
    active: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30
    headers: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    delivery_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def is_active(self) -> bool:
        """Check if endpoint is active"""
        return self.active
    
    def subscribes_to(self, event_type: EventType) -> bool:
        """Check if endpoint subscribes to an event type"""
        return event_type in self.events
    
    def get_success_rate(self) -> float:
        """Calculate delivery success rate"""
        if self.delivery_count == 0:
            return 1.0
        return self.success_count / self.delivery_count


@dataclass
class WebhookEvent:
    """A webhook event to be delivered"""
    id: str
    event_type: EventType
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    source_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert event to webhook payload"""
        return {
            "id": self.id,
            "event": self.event_type.value,
            "data": self.data,
            "timestamp": self.created_at.isoformat() + "Z",
            "source": self.source_agent,
            "correlationId": self.correlation_id
        }


@dataclass
class WebhookDelivery:
    """A webhook delivery attempt"""
    id: str
    webhook_id: str
    event_id: str
    url: str
    status: WebhookStatus
    attempt: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    next_retry: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    
    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if delivery has expired"""
        age = datetime.utcnow() - self.created_at
        return age > timedelta(hours=max_age_hours)
    
    def should_retry(self, max_retries: int = 3) -> bool:
        """Check if delivery should be retried"""
        return (
            self.status == WebhookStatus.FAILED and
            self.attempt < max_retries and
            not self.is_expired()
        )


class WebhookManager:
    """
    Manages webhook endpoints and event delivery.
    
    Provides functionality for:
    - Registering and managing webhook endpoints
    - Publishing events to subscribers
    - Retry logic for failed deliveries
    - Webhook signature verification
    """
    
    def __init__(self, default_timeout: int = 30, max_retries: int = 3):
        """
        Initialize webhook manager.
        
        Args:
            default_timeout: Default HTTP timeout in seconds
            max_retries: Default maximum retry attempts
        """
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.client: Optional[httpx.AsyncClient] = None
        
        logger.debug("Webhook manager initialized")
    
    async def start(self):
        """Start the webhook manager (initialize HTTP client)"""
        if HTTPX_AVAILABLE:
            self.client = httpx.AsyncClient(timeout=self.default_timeout)
            logger.info("Webhook manager started with HTTP client")
        else:
            logger.warning("httpx not available. Webhook delivery will be disabled.")
    
    async def stop(self):
        """Stop the webhook manager (cleanup resources)"""
        if self.client:
            await self.client.aclose()
            self.client = None
        logger.info("Webhook manager stopped")
    
    def register_webhook(
        self,
        url: str,
        events: List[Union[EventType, str]],
        secret: Optional[str] = None,
        webhook_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[int] = None
    ) -> WebhookEndpoint:
        """
        Register a new webhook endpoint.
        
        Args:
            url: Webhook URL
            events: List of event types to subscribe to
            secret: Secret for signature verification
            webhook_id: Unique webhook identifier (auto-generated if None)
            headers: Additional HTTP headers
            max_retries: Maximum retry attempts
            timeout_seconds: HTTP timeout
            
        Returns:
            Created WebhookEndpoint
            
        Raises:
            ValidationError: If webhook configuration is invalid
        """
        if webhook_id is None:
            webhook_id = f"webhook-{uuid.uuid4()}"
        
        if webhook_id in self.endpoints:
            raise ValidationError(f"Webhook '{webhook_id}' already exists")
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValidationError(f"Invalid webhook URL: {url}")
        
        if parsed_url.scheme not in ['http', 'https']:
            raise ValidationError("Webhook URL must use HTTP or HTTPS")
        
        # Convert string events to EventType
        event_types = []
        for event in events:
            if isinstance(event, str):
                try:
                    event_types.append(EventType(event))
                except ValueError:
                    raise ValidationError(f"Unknown event type: {event}")
            else:
                event_types.append(event)
        
        # Create webhook endpoint
        endpoint = WebhookEndpoint(
            id=webhook_id,
            url=url,
            events=event_types,
            secret=secret,
            headers=headers or {},
            max_retries=max_retries or self.max_retries,
            timeout_seconds=timeout_seconds or self.default_timeout
        )
        
        self.endpoints[webhook_id] = endpoint
        
        logger.info(f"Registered webhook: {webhook_id} for events: {[e.value for e in event_types]}")
        return endpoint
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """
        Unregister a webhook endpoint.
        
        Args:
            webhook_id: Webhook identifier
            
        Returns:
            True if webhook was removed, False if not found
        """
        if webhook_id in self.endpoints:
            del self.endpoints[webhook_id]
            logger.info(f"Unregistered webhook: {webhook_id}")
            return True
        return False
    
    def get_webhook(self, webhook_id: str) -> Optional[WebhookEndpoint]:
        """Get webhook endpoint by ID"""
        return self.endpoints.get(webhook_id)
    
    def list_webhooks(self) -> List[WebhookEndpoint]:
        """List all registered webhook endpoints"""
        return list(self.endpoints.values())
    
    def get_webhooks_for_event(self, event_type: EventType) -> List[WebhookEndpoint]:
        """Get all active webhooks that subscribe to an event type"""
        return [
            endpoint for endpoint in self.endpoints.values()
            if endpoint.is_active() and endpoint.subscribes_to(event_type)
        ]
    
    async def publish_event(
        self,
        event_type: Union[EventType, str],
        data: Dict[str, Any],
        source_agent: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[str]:
        """
        Publish an event to all subscribed webhooks.
        
        Args:
            event_type: Type of event
            data: Event data
            source_agent: Source agent identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            List of delivery IDs
        """
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
            except ValueError:
                logger.error(f"Unknown event type: {event_type}")
                return []
        
        # Create event
        event = WebhookEvent(
            id=f"event-{uuid.uuid4()}",
            event_type=event_type,
            data=data,
            source_agent=source_agent,
            correlation_id=correlation_id
        )
        
        # Find subscribed webhooks
        webhooks = self.get_webhooks_for_event(event_type)
        
        if not webhooks:
            logger.debug(f"No webhooks subscribed to event: {event_type.value}")
            return []
        
        # Deliver to each webhook
        delivery_ids = []
        for webhook in webhooks:
            delivery_id = await self._deliver_webhook(webhook, event)
            if delivery_id:
                delivery_ids.append(delivery_id)
        
        logger.info(f"Published event {event.id} to {len(delivery_ids)} webhooks")
        return delivery_ids
    
    async def _deliver_webhook(
        self,
        webhook: WebhookEndpoint,
        event: WebhookEvent
    ) -> Optional[str]:
        """
        Deliver an event to a specific webhook.
        
        Args:
            webhook: Webhook endpoint
            event: Event to deliver
            
        Returns:
            Delivery ID if delivery was attempted, None otherwise
        """
        if not self.client:
            logger.warning("HTTP client not available. Cannot deliver webhook.")
            return None
        
        # Create delivery record
        delivery = WebhookDelivery(
            id=f"delivery-{uuid.uuid4()}",
            webhook_id=webhook.id,
            event_id=event.id,
            url=webhook.url
        )
        
        self.deliveries[delivery.id] = delivery
        
        # Attempt delivery
        await self._attempt_delivery(webhook, event, delivery)
        
        return delivery.id
    
    async def _attempt_delivery(
        self,
        webhook: WebhookEndpoint,
        event: WebhookEvent,
        delivery: WebhookDelivery
    ):
        """
        Attempt to deliver a webhook event.
        
        Args:
            webhook: Webhook endpoint
            event: Event to deliver
            delivery: Delivery record
        """
        try:
            # Prepare payload
            payload = event.to_payload()
            payload_json = json.dumps(payload, default=str)
            
            # Prepare headers
            headers = webhook.headers.copy()
            headers["Content-Type"] = "application/json"
            headers["User-Agent"] = "ACP-Webhook/1.0"
            headers["X-Webhook-ID"] = webhook.id
            headers["X-Event-ID"] = event.id
            headers["X-Delivery-ID"] = delivery.id
            
            # Add signature if secret is configured
            if webhook.secret:
                signature = self._generate_signature(payload_json, webhook.secret)
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            # Make HTTP request
            delivery.status = WebhookStatus.PENDING
            
            response = await self.client.post(
                webhook.url,
                content=payload_json,
                headers=headers,
                timeout=webhook.timeout_seconds
            )
            
            # Update delivery record
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000]  # Limit response body size
            delivery.delivered_at = datetime.utcnow()
            
            # Check if delivery was successful
            if 200 <= response.status_code < 300:
                delivery.status = WebhookStatus.DELIVERED
                webhook.success_count += 1
                logger.debug(f"Webhook delivered successfully: {delivery.id}")
            else:
                delivery.status = WebhookStatus.FAILED
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                webhook.failure_count += 1
                logger.warning(f"Webhook delivery failed: {delivery.id} - {delivery.error_message}")
                
                # Schedule retry if appropriate
                if delivery.should_retry(webhook.max_retries):
                    await self._schedule_retry(webhook, event, delivery)
            
            # Update webhook stats
            webhook.delivery_count += 1
            webhook.last_used = datetime.utcnow()
            
        except Exception as e:
            # Handle delivery error
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = str(e)
            webhook.failure_count += 1
            webhook.delivery_count += 1
            
            logger.error(f"Webhook delivery error: {delivery.id} - {e}")
            
            # Schedule retry if appropriate
            if delivery.should_retry(webhook.max_retries):
                await self._schedule_retry(webhook, event, delivery)
    
    async def _schedule_retry(
        self,
        webhook: WebhookEndpoint,
        event: WebhookEvent,
        delivery: WebhookDelivery
    ):
        """
        Schedule a retry for a failed webhook delivery.
        
        Args:
            webhook: Webhook endpoint
            event: Event to deliver
            delivery: Delivery record
        """
        # Calculate exponential backoff delay
        delay_seconds = min(60 * (2 ** (delivery.attempt - 1)), 3600)  # Max 1 hour
        delivery.next_retry = datetime.utcnow() + timedelta(seconds=delay_seconds)
        delivery.status = WebhookStatus.RETRYING
        delivery.attempt += 1
        
        logger.info(f"Scheduled webhook retry: {delivery.id} in {delay_seconds}s (attempt {delivery.attempt})")
        
        # Schedule the retry (in a real implementation, this would use a task queue)
        asyncio.create_task(self._retry_delivery(webhook, event, delivery, delay_seconds))
    
    async def _retry_delivery(
        self,
        webhook: WebhookEndpoint,
        event: WebhookEvent,
        delivery: WebhookDelivery,
        delay_seconds: float
    ):
        """
        Retry a failed webhook delivery after a delay.
        
        Args:
            webhook: Webhook endpoint
            event: Event to deliver  
            delivery: Delivery record
            delay_seconds: Delay before retry
        """
        await asyncio.sleep(delay_seconds)
        
        # Check if delivery is still valid
        if delivery.is_expired():
            delivery.status = WebhookStatus.EXPIRED
            logger.warning(f"Webhook delivery expired: {delivery.id}")
            return
        
        # Attempt delivery again
        await self._attempt_delivery(webhook, event, delivery)
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """
        Generate HMAC signature for webhook verification.
        
        Args:
            payload: Webhook payload
            secret: Webhook secret
            
        Returns:
            HMAC signature
        """
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Webhook payload
            signature: Provided signature
            secret: Webhook secret
            
        Returns:
            True if signature is valid
        """
        expected_signature = self._generate_signature(payload, secret)
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        return hmac.compare_digest(expected_signature, signature)
    
    def get_delivery_status(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery status by ID"""
        return self.deliveries.get(delivery_id)
    
    def get_webhook_stats(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a webhook endpoint.
        
        Args:
            webhook_id: Webhook identifier
            
        Returns:
            Dictionary with webhook statistics
        """
        webhook = self.endpoints.get(webhook_id)
        if not webhook:
            return None
        
        return {
            "webhookId": webhook.id,
            "url": webhook.url,
            "active": webhook.active,
            "events": [e.value for e in webhook.events],
            "deliveryCount": webhook.delivery_count,
            "successCount": webhook.success_count,
            "failureCount": webhook.failure_count,
            "successRate": webhook.get_success_rate(),
            "lastUsed": webhook.last_used.isoformat() + "Z" if webhook.last_used else None,
            "createdAt": webhook.created_at.isoformat() + "Z"
        }
    
    def cleanup_old_deliveries(self, max_age_hours: int = 48):
        """
        Remove old delivery records to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age of deliveries to keep
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        old_deliveries = [
            delivery_id for delivery_id, delivery in self.deliveries.items()
            if delivery.created_at < cutoff_time
        ]
        
        for delivery_id in old_deliveries:
            del self.deliveries[delivery_id]
        
        if old_deliveries:
            logger.info(f"Cleaned up {len(old_deliveries)} old webhook deliveries")


class WebhookJsonRpcProcessor:
    """
    JSON-RPC processor with webhook notification support.
    
    Automatically publishes webhook events for ACP method responses.
    """
    
    def __init__(self, webhook_manager: WebhookManager):
        """
        Initialize webhook processor.
        
        Args:
            webhook_manager: Webhook manager instance
        """
        self.webhook_manager = webhook_manager
        self.base_processor = JsonRpcProcessor()
        
        # Register webhook notification handlers
        self._register_notification_handlers()
    
    def _register_notification_handlers(self):
        """Register default notification method handlers"""
        
        async def handle_task_notification(params, context):
            """Handle task.notification method"""
            notification_params = TaskNotificationParams.model_validate(params)
            
            # Determine event type based on task status
            event_type_map = {
                "SUBMITTED": EventType.TASK_CREATED,
                "WORKING": EventType.TASK_UPDATED,
                "COMPLETED": EventType.TASK_COMPLETED,
                "FAILED": EventType.TASK_FAILED,
                "CANCELED": EventType.TASK_UPDATED
            }
            
            task_status = notification_params.task.status
            event_type = event_type_map.get(task_status, EventType.TASK_UPDATED)
            
            # Publish webhook event
            await self.webhook_manager.publish_event(
                event_type=event_type,
                data={
                    "task": notification_params.task.model_dump(by_alias=True),
                    "message": notification_params.message.model_dump(by_alias=True) if notification_params.message else None
                },
                source_agent=getattr(context, 'agent_id', None),
                correlation_id=getattr(context, 'correlation_id', None)
            )
            
            return {
                "type": "success",
                "message": "Notification processed"
            }
        
        async def handle_stream_chunk(params, context):
            """Handle stream.chunk method"""
            chunk_params = StreamChunkParams.model_validate(params)
            
            # Publish webhook event for stream chunk
            await self.webhook_manager.publish_event(
                event_type=EventType.STREAM_MESSAGE,
                data={
                    "streamId": chunk_params.stream_id,
                    "chunk": chunk_params.chunk.model_dump(by_alias=True)
                },
                source_agent=getattr(context, 'agent_id', None),
                correlation_id=getattr(context, 'correlation_id', None)
            )
            
            return {
                "type": "success",
                "message": "Stream chunk processed"
            }
        
        # Register handlers
        self.base_processor.register_handler("task.notification", handle_task_notification)
        self.base_processor.register_handler("stream.chunk", handle_stream_chunk)
    
    async def process_request(
        self,
        request_data: Dict[str, Any],
        context,
        auto_notify: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Process JSON-RPC request with automatic webhook notifications.
        
        Args:
            request_data: JSON-RPC request data
            context: Request context
            auto_notify: Whether to automatically send webhook notifications
            
        Returns:
            JSON-RPC response or None for notifications
        """
        response = await self.base_processor.process_request(request_data, context)
        
        # Automatically publish webhook events for certain methods
        if auto_notify and response and "result" in response:
            method = request_data.get("method", "")
            
            if method == "tasks.create":
                await self.webhook_manager.publish_event(
                    event_type=EventType.TASK_CREATED,
                    data=response["result"],
                    source_agent=getattr(context, 'agent_id', None),
                    correlation_id=getattr(context, 'correlation_id', None)
                )
            elif method == "stream.start":
                await self.webhook_manager.publish_event(
                    event_type=EventType.STREAM_STARTED,
                    data=response["result"],
                    source_agent=getattr(context, 'agent_id', None),
                    correlation_id=getattr(context, 'correlation_id', None)
                )
        
        return response


# Utility functions for webhooks

def create_webhook_manager(
    default_timeout: int = 30,
    max_retries: int = 3
) -> WebhookManager:
    """
    Create a new webhook manager instance.
    
    Args:
        default_timeout: Default HTTP timeout
        max_retries: Default maximum retry attempts
        
    Returns:
        Configured WebhookManager instance
    """
    return WebhookManager(default_timeout, max_retries)


async def publish_task_event(
    webhook_manager: WebhookManager,
    task_id: str,
    status: str,
    task_data: Dict[str, Any],
    source_agent: Optional[str] = None
):
    """
    Publish a task-related webhook event.
    
    Args:
        webhook_manager: Webhook manager instance
        task_id: Task identifier
        status: Task status
        task_data: Task data
        source_agent: Source agent identifier
    """
    event_type_map = {
        "SUBMITTED": EventType.TASK_CREATED,
        "WORKING": EventType.TASK_UPDATED,
        "COMPLETED": EventType.TASK_COMPLETED,
        "FAILED": EventType.TASK_FAILED
    }
    
    event_type = event_type_map.get(status, EventType.TASK_UPDATED)
    
    await webhook_manager.publish_event(
        event_type=event_type,
        data={
            "taskId": task_id,
            "status": status,
            "task": task_data
        },
        source_agent=source_agent
    )
