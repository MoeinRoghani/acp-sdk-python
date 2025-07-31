"""
ACP Testing Utilities (Simplified)

Provides mock clients, test utilities, and helpers for testing ACP 
client and server communication without agent framework dependencies.
"""

import json
import logging
import time
import uuid
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

from ..client.acp_client import ACPClient
from ..server.acp_server import ACPServer
from ..core.json_rpc import JsonRpcContext, JsonRpcProcessor
from ..models.generated import (
    TasksCreateParams, TasksSendParams, TasksGetParams,
    StreamStartParams, StreamMessageParams, StreamEndParams,
    TaskObject, StreamObject, Message, Part, Status
)
from ..exceptions import ACPException


logger = logging.getLogger(__name__)


@dataclass
class TestConfig:
    """Configuration for testing"""
    timeout: float = 30.0
    base_url: str = "https://test-agent.example.com"
    oauth_token: str = "test-token"
    log_level: str = "INFO"


class MockACPClient:
    """
    Mock ACP client for testing.
    
    Records calls and returns predefined responses without
    making actual HTTP requests.
    """
    
    def __init__(
        self,
        base_url: str = "https://mock-agent.example.com",
        responses: Optional[Dict[str, Dict[str, Any]]] = None,
        delays: Optional[Dict[str, float]] = None,
        should_fail: Optional[Dict[str, Exception]] = None
    ):
        """
        Initialize mock client.
        
        Args:
            base_url: Mock base URL
            responses: Predefined responses by method
            delays: Delays by method (in seconds)
            should_fail: Exceptions to raise by method
        """
        self.base_url = base_url
        self.responses = responses or {}
        self.delays = delays or {}
        self.should_fail = should_fail or {}
        self.call_history: List[Dict[str, Any]] = []
    
    async def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock JSON-RPC call"""
        # Record call
        call_record = {
            "method": method,
            "params": params,
            "timestamp": datetime.utcnow().isoformat(),
            "call_id": str(uuid.uuid4())
        }
        self.call_history.append(call_record)
        
        # Add delay if specified
        if method in self.delays:
            await asyncio.sleep(self.delays[method])
        
        # Raise exception if specified
        if method in self.should_fail:
            raise self.should_fail[method]
        
        # Return predefined response or default
        if method in self.responses:
            return self.responses[method]
        
        # Default responses
        if method == "tasks.create":
            return {
                "type": "task",
                "taskId": f"mock-task-{uuid.uuid4()}",
                "status": "SUBMITTED",
                "submittedAt": datetime.utcnow().isoformat()
            }
        elif method == "tasks.send":
            return {
                "type": "success", 
                "message": "Message sent successfully"
            }
        elif method == "tasks.get":
            return {
                "type": "task",
                "taskId": params.get("taskId", "unknown") if params else "unknown",
                "status": "COMPLETED",
                "completedAt": datetime.utcnow().isoformat()
            }
        else:
            return {"type": "success", "message": f"Mock response for {method}"}
    
    async def tasks_create(self, params: TasksCreateParams) -> Dict[str, Any]:
        """Mock task creation"""
        return await self.call("tasks.create", params.model_dump())
    
    async def tasks_send(self, params: TasksSendParams) -> Dict[str, Any]:
        """Mock task message sending"""
        return await self.call("tasks.send", params.model_dump())
    
    async def tasks_get(self, params: TasksGetParams) -> Dict[str, Any]:
        """Mock task retrieval"""
        return await self.call("tasks.get", params.model_dump())
    
    def get_call_count(self, method: Optional[str] = None) -> int:
        """Get number of calls (total or for specific method)"""
        if method is None:
            return len(self.call_history)
        return len([call for call in self.call_history if call["method"] == method])
    
    def get_last_call(self, method: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get last call (total or for specific method)"""
        if method is None:
            return self.call_history[-1] if self.call_history else None
        
        method_calls = [call for call in self.call_history if call["method"] == method]
        return method_calls[-1] if method_calls else None
    
    def reset_call_history(self):
        """Clear call history"""
        self.call_history.clear()


# Test Data Factories

def create_test_message(
    text: str = "Test message",
    role: str = "user",
    message_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a test message"""
    return {
        "messageId": message_id or f"msg-{uuid.uuid4()}",
        "role": role,
        "parts": [
            {
                "type": "TextPart",
                "text": text
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


def create_test_task_params(
    message: Optional[str] = None,
    agent_id: str = "test-agent",
    priority: str = "MEDIUM"
) -> Dict[str, Any]:
    """Create test TasksCreateParams"""
    return {
        "agentId": agent_id,
        "initialMessage": create_test_message(message or "Test task"),
        "priority": priority,
        "metadata": {"test": True}
    }


def create_test_task_object(
    task_id: Optional[str] = None,
    status: str = "SUBMITTED",
    agent_id: str = "test-agent"
) -> Dict[str, Any]:
    """Create test task object"""
    return {
        "type": "task",
        "taskId": task_id or f"task-{uuid.uuid4()}",
        "status": status,
        "priority": "MEDIUM",
        "submittedAt": datetime.utcnow().isoformat(),
        "agentId": agent_id,
        "metadata": {"test": True}
    }


def create_test_stream_params(
    agent_id: str = "test-agent",
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Create test StreamStartParams"""
    return {
        "agentId": agent_id,
        "initialMessage": create_test_message(message or "Test stream"),
        "metadata": {"test": True}
    }


# Assertion Helpers

def assert_task_response(
    response: Dict[str, Any],
    expected_status: Optional[str] = None,
    expected_task_id: Optional[str] = None
):
    """Assert task response has expected structure and values"""
    assert "type" in response, "Response missing 'type' field"
    assert response["type"] == "task", f"Expected type 'task', got '{response['type']}'"
    
    assert "taskId" in response, "Response missing 'taskId' field"
    assert "status" in response, "Response missing 'status' field"
    
    if expected_status:
        assert response["status"] == expected_status, f"Expected status '{expected_status}', got '{response['status']}'"
    
    if expected_task_id:
        assert response["taskId"] == expected_task_id, f"Expected task ID '{expected_task_id}', got '{response['taskId']}'"


def assert_stream_response(
    response: Dict[str, Any],
    expected_status: Optional[str] = None,
    expected_stream_id: Optional[str] = None
):
    """Assert stream response has expected structure and values"""
    assert "type" in response, "Response missing 'type' field"
    assert response["type"] == "stream", f"Expected type 'stream', got '{response['type']}'"
    
    assert "streamId" in response, "Response missing 'streamId' field"
    assert "status" in response, "Response missing 'status' field"
    
    if expected_status:
        assert response["status"] == expected_status, f"Expected status '{expected_status}', got '{response['status']}'"
    
    if expected_stream_id:
        assert response["streamId"] == expected_stream_id, f"Expected stream ID '{expected_stream_id}', got '{response['streamId']}'"


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 5.0,
    interval: float = 0.1,
    description: str = "condition"
) -> bool:
    """Wait for a condition to become true"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(interval)
    
    raise TimeoutError(f"Timeout waiting for {description} after {timeout}s")


# Pytest Fixtures (if pytest is available)

if PYTEST_AVAILABLE:
    @pytest.fixture
    def mock_client():
        """Pytest fixture for mock ACP client"""
        return MockACPClient()
    
    @pytest.fixture
    def test_config():
        """Pytest fixture for test configuration"""
        return TestConfig()


# Context Managers and Utilities

class AsyncContextManager:
    """Helper for testing async context managers"""
    
    def __init__(self, target):
        self.target = target
        self.result = None
        self.exception = None
    
    async def __aenter__(self):
        try:
            if hasattr(self.target, '__aenter__'):
                self.result = await self.target.__aenter__()
            else:
                self.result = self.target
            return self.result
        except Exception as e:
            self.exception = e
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.target, '__aexit__'):
            return await self.target.__aexit__(exc_type, exc_val, exc_tb)
        return False


class PerformanceTimer:
    """Simple performance timer for testing"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def start(self):
        """Start timing"""
        self.start_time = time.time()
        self.end_time = None
        self.duration = None
    
    def stop(self):
        """Stop timing"""
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return self.duration
    
    def assert_faster_than(self, max_duration: float):
        """Assert that operation was faster than max_duration"""
        assert self.duration < max_duration, f"Operation took {self.duration:.3f}s, expected < {max_duration}s"
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Simple Server Testing Utilities

class SimpleJsonRpcServer:
    """
    Simple JSON-RPC server for testing without FastAPI dependencies.
    
    Note: For production testing, use ACPServer with FastAPI test client.
    """
    
    def __init__(self):
        self.processor = JsonRpcProcessor()
        self.handlers = {}
        self.call_history = []
    
    def register_handler(self, method: str, handler: Callable):
        """Register a method handler"""
        self.handlers[method] = handler
        
        async def wrapper(params, context):
            result = await handler(params, context)
            self.call_history.append({
                "method": method,
                "params": params,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            return result
        
        self.processor.register_method(method, wrapper)
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a JSON-RPC request"""
        context = JsonRpcContext(
            correlation_id=str(uuid.uuid4()),
            user_id="test-user",
            agent_id="test-agent"
        )
        
        return await self.processor.process_request(request, context)
    
    def get_call_history(self, method: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get call history for all methods or specific method"""
        if method is None:
            return self.call_history.copy()
        return [call for call in self.call_history if call["method"] == method]
    
    def reset_history(self):
        """Clear call history"""
        self.call_history.clear()


# Performance Testing Utilities

async def measure_client_performance(
    client: ACPClient,
    method: str,
    params: Dict[str, Any],
    num_requests: int = 10,
    concurrency: int = 1
) -> Dict[str, Any]:
    """
    Measure client performance for a specific method.
    
    Args:
        client: ACP client to test
        method: Method to call
        params: Parameters for the method
        num_requests: Total number of requests
        concurrency: Number of concurrent requests
        
    Returns:
        Performance statistics
    """
    start_time = time.time()
    completed = 0
    errors = 0
    
    async def make_request():
        nonlocal completed, errors
        try:
            await client.call(method, params)
            completed += 1
        except Exception as e:
            errors += 1
            logger.error(f"Request failed: {e}")
    
    # Run requests in batches based on concurrency
    tasks = []
    for i in range(num_requests):
        tasks.append(make_request())
        
        # Process in batches
        if len(tasks) >= concurrency or i == num_requests - 1:
            await asyncio.gather(*tasks, return_exceptions=True)
            tasks = []
    
    end_time = time.time()
    duration = end_time - start_time
    
    return {
        "total_requests": num_requests,
        "completed": completed,
        "errors": errors,
        "duration_seconds": duration,
        "requests_per_second": completed / duration if duration > 0 else 0,
        "success_rate": completed / num_requests if num_requests > 0 else 0
    } 