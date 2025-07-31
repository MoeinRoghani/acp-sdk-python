"""
ACP Streaming Support

Provides WebSocket-based real-time communication capabilities for ACP agents.
Supports bidirectional streaming, message chunking, and connection management.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Callable, Any, AsyncGenerator, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    from websockets.exceptions import ConnectionClosed, WebSocketException
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WebSocketServerProtocol = None
    ConnectionClosed = Exception
    WebSocketException = Exception
    WEBSOCKETS_AVAILABLE = False

from ..models.generated import StreamObject, StreamStartParams, StreamMessageParams, StreamEndParams
from ..core.json_rpc import JsonRpcContext, JsonRpcError, JsonRpcProcessor
from ..exceptions import StreamNotFound, StreamAlreadyClosed


logger = logging.getLogger(__name__)


class StreamStatus(Enum):
    """Stream status values"""
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"
    ERROR = "ERROR"


@dataclass
class StreamChunk:
    """A chunk of streaming data"""
    stream_id: str
    sequence: int
    data: Any
    is_final: bool = False
    chunk_type: str = "data"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary"""
        return {
            "streamId": self.stream_id,
            "sequence": self.sequence,
            "data": self.data,
            "isFinal": self.is_final,
            "chunkType": self.chunk_type,
            "timestamp": self.timestamp.isoformat() + "Z",
            "metadata": self.metadata
        }


@dataclass
class StreamConnection:
    """Represents an active streaming connection"""
    stream_id: str
    websocket: Optional[WebSocketServerProtocol]
    status: StreamStatus
    participants: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    sequence: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if stream is active"""
        return self.status == StreamStatus.ACTIVE
    
    def is_closed(self) -> bool:
        """Check if stream is closed"""
        return self.status in [StreamStatus.CLOSED, StreamStatus.ERROR]


class StreamManager:
    """
    Manages WebSocket streaming connections for ACP communication.
    
    Provides functionality for:
    - Creating and managing stream connections
    - Sending and receiving streaming data
    - Managing participants and permissions
    - Handling connection lifecycle
    """
    
    def __init__(self):
        """Initialize stream manager"""
        self.streams: Dict[str, StreamConnection] = {}
        self.handlers: Dict[str, Callable] = {}
        self.middleware: List[Callable] = []
        logger.debug("Stream manager initialized")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware for stream processing"""
        self.middleware.append(middleware)
    
    def register_handler(self, event_type: str, handler: Callable):
        """
        Register handler for stream events.
        
        Args:
            event_type: Type of stream event (start, message, chunk, end, etc.)
            handler: Handler function
        """
        self.handlers[event_type] = handler
        logger.debug(f"Registered stream handler for: {event_type}")
    
    async def create_stream(
        self,
        stream_id: Optional[str] = None,
        participants: Optional[List[str]] = None,
        websocket: Optional[WebSocketServerProtocol] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StreamConnection:
        """
        Create a new streaming connection.
        
        Args:
            stream_id: Unique stream identifier (auto-generated if None)
            participants: List of participant identifiers
            websocket: WebSocket connection (optional for HTTP-based streams)
            metadata: Additional stream metadata
            
        Returns:
            Created StreamConnection
            
        Raises:
            ValueError: If stream_id already exists
        """
        if stream_id is None:
            stream_id = f"stream-{uuid.uuid4()}"
        
        if stream_id in self.streams:
            raise ValueError(f"Stream '{stream_id}' already exists")
        
        # Create stream connection
        connection = StreamConnection(
            stream_id=stream_id,
            websocket=websocket,
            status=StreamStatus.INITIALIZING,
            participants=participants or [],
            metadata=metadata or {}
        )
        
        self.streams[stream_id] = connection
        
        logger.info(f"Created stream: {stream_id}")
        
        # Call start handler if registered
        if "start" in self.handlers:
            try:
                await self.handlers["start"](connection)
            except Exception as e:
                logger.error(f"Error in stream start handler: {e}")
                connection.status = StreamStatus.ERROR
                raise
        
        # Mark as active
        connection.status = StreamStatus.ACTIVE
        
        return connection
    
    async def close_stream(self, stream_id: str, reason: str = "closed") -> bool:
        """
        Close a streaming connection.
        
        Args:
            stream_id: Stream identifier
            reason: Reason for closing
            
        Returns:
            True if stream was closed, False if not found
        """
        if stream_id not in self.streams:
            return False
        
        connection = self.streams[stream_id]
        
        if connection.is_closed():
            return True
        
        # Call end handler if registered
        if "end" in self.handlers:
            try:
                await self.handlers["end"](connection, reason)
            except Exception as e:
                logger.error(f"Error in stream end handler: {e}")
        
        # Close WebSocket connection if exists
        if connection.websocket and not connection.websocket.closed:
            try:
                await connection.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket for stream {stream_id}: {e}")
        
        # Mark as closed
        connection.status = StreamStatus.CLOSED
        
        logger.info(f"Closed stream: {stream_id} (reason: {reason})")
        return True
    
    async def send_chunk(
        self,
        stream_id: str,
        data: Any,
        chunk_type: str = "data",
        is_final: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a data chunk to a stream.
        
        Args:
            stream_id: Stream identifier
            data: Data to send
            chunk_type: Type of chunk (data, control, error, etc.)
            is_final: Whether this is the final chunk
            metadata: Additional chunk metadata
            
        Returns:
            True if chunk was sent, False if stream not found or inactive
        """
        if stream_id not in self.streams:
            logger.warning(f"Attempted to send chunk to non-existent stream: {stream_id}")
            return False
        
        connection = self.streams[stream_id]
        
        if not connection.is_active():
            logger.warning(f"Attempted to send chunk to inactive stream: {stream_id}")
            return False
        
        # Create chunk
        chunk = StreamChunk(
            stream_id=stream_id,
            sequence=connection.sequence,
            data=data,
            chunk_type=chunk_type,
            is_final=is_final,
            metadata=metadata or {}
        )
        
        connection.sequence += 1
        connection.last_activity = datetime.utcnow()
        
        # Send via WebSocket if available
        if connection.websocket and not connection.websocket.closed:
            try:
                message = {
                    "type": "chunk",
                    "chunk": chunk.to_dict()
                }
                await connection.websocket.send(json.dumps(message))
                logger.debug(f"Sent chunk {chunk.sequence} to stream {stream_id}")
            except (ConnectionClosed, WebSocketException) as e:
                logger.warning(f"WebSocket connection lost for stream {stream_id}: {e}")
                connection.status = StreamStatus.ERROR
                return False
        
        # Call chunk handler if registered
        if "chunk" in self.handlers:
            try:
                await self.handlers["chunk"](connection, chunk)
            except Exception as e:
                logger.error(f"Error in stream chunk handler: {e}")
        
        # Close stream if this is the final chunk
        if is_final:
            await self.close_stream(stream_id, "completed")
        
        return True
    
    async def receive_chunk(self, stream_id: str, chunk_data: Dict[str, Any]) -> bool:
        """
        Process a received chunk from a stream.
        
        Args:
            stream_id: Stream identifier
            chunk_data: Received chunk data
            
        Returns:
            True if chunk was processed, False otherwise
        """
        if stream_id not in self.streams:
            logger.warning(f"Received chunk for non-existent stream: {stream_id}")
            return False
        
        connection = self.streams[stream_id]
        connection.last_activity = datetime.utcnow()
        
        # Apply middleware
        for middleware in self.middleware:
            try:
                chunk_data = await middleware(chunk_data, connection)
            except Exception as e:
                logger.error(f"Error in stream middleware: {e}")
                return False
        
        # Call message handler if registered
        if "message" in self.handlers:
            try:
                await self.handlers["message"](connection, chunk_data)
            except Exception as e:
                logger.error(f"Error in stream message handler: {e}")
                return False
        
        return True
    
    def get_stream(self, stream_id: str) -> Optional[StreamConnection]:
        """Get stream connection by ID"""
        return self.streams.get(stream_id)
    
    def list_streams(self) -> List[str]:
        """List all stream IDs"""
        return list(self.streams.keys())
    
    def get_active_streams(self) -> List[StreamConnection]:
        """Get all active stream connections"""
        return [conn for conn in self.streams.values() if conn.is_active()]
    
    def cleanup_closed_streams(self):
        """Remove closed streams from memory"""
        closed_streams = [
            stream_id for stream_id, conn in self.streams.items()
            if conn.is_closed()
        ]
        
        for stream_id in closed_streams:
            del self.streams[stream_id]
            logger.debug(f"Cleaned up closed stream: {stream_id}")
    
    async def stream_data(
        self,
        stream_id: str,
        data_generator: AsyncGenerator[Any, None],
        chunk_size: int = 1024
    ):
        """
        Stream data from an async generator.
        
        Args:
            stream_id: Stream identifier
            data_generator: Async generator yielding data chunks
            chunk_size: Maximum size of each chunk
        """
        try:
            async for data in data_generator:
                success = await self.send_chunk(stream_id, data)
                if not success:
                    logger.warning(f"Failed to send chunk to stream {stream_id}")
                    break
                    
                # Small delay to prevent overwhelming the connection
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error streaming data to {stream_id}: {e}")
            await self.send_chunk(
                stream_id,
                {"error": str(e)},
                chunk_type="error",
                is_final=True
            )
        finally:
            # Send final chunk
            await self.send_chunk(stream_id, None, chunk_type="end", is_final=True)


class StreamingJsonRpcProcessor:
    """
    JSON-RPC processor with streaming support.
    
    Extends the base JSON-RPC processor to handle streaming methods
    and WebSocket connections.
    """
    
    def __init__(self, stream_manager: StreamManager):
        """
        Initialize streaming processor.
        
        Args:
            stream_manager: Stream manager instance
        """
        self.stream_manager = stream_manager
        self.base_processor = JsonRpcProcessor()
        
        # Register streaming method handlers
        self._register_streaming_handlers()
    
    def _register_streaming_handlers(self):
        """Register default streaming method handlers"""
        
        async def handle_stream_start(params, context: JsonRpcContext):
            """Handle stream.start method"""
            stream_params = StreamStartParams.model_validate(params)
            
            # Create stream
            connection = await self.stream_manager.create_stream(
                participants=stream_params.participants,
                metadata={"topic": getattr(stream_params, 'topic', None)}
            )
            
            return {
                "type": "stream",
                "stream": {
                    "streamId": connection.stream_id,
                    "status": connection.status.value,
                    "participants": connection.participants,
                    "createdAt": connection.created_at.isoformat() + "Z"
                }
            }
        
        async def handle_stream_message(params, context: JsonRpcContext):
            """Handle stream.message method"""
            msg_params = StreamMessageParams.model_validate(params)
            
            # Send message as chunk
            success = await self.stream_manager.send_chunk(
                stream_id=msg_params.stream_id,
                data=msg_params.message.model_dump(by_alias=True),
                chunk_type="message"
            )
            
            if not success:
                raise JsonRpcError(-40003, f"Stream not found: {msg_params.stream_id}")
            
            return {
                "type": "success",
                "message": "Message sent to stream"
            }
        
        async def handle_stream_end(params, context: JsonRpcContext):
            """Handle stream.end method"""
            end_params = StreamEndParams.model_validate(params)
            
            success = await self.stream_manager.close_stream(
                stream_id=end_params.stream_id,
                reason=getattr(end_params, 'reason', 'ended')
            )
            
            if not success:
                raise JsonRpcError(-40003, f"Stream not found: {end_params.stream_id}")
            
            return {
                "type": "success",
                "message": "Stream ended"
            }
        
        # Register handlers
        self.base_processor.register_handler("stream.start", handle_stream_start)
        self.base_processor.register_handler("stream.message", handle_stream_message)
        self.base_processor.register_handler("stream.end", handle_stream_end)
    
    async def process_request(
        self,
        request_data: Dict[str, Any],
        context: JsonRpcContext,
        websocket: Optional[WebSocketServerProtocol] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process JSON-RPC request with streaming support.
        
        Args:
            request_data: JSON-RPC request data
            context: Request context
            websocket: Optional WebSocket connection
            
        Returns:
            JSON-RPC response or None for notifications
        """
        # Add WebSocket to context for streaming methods
        if websocket:
            context.websocket = websocket
        
        return await self.base_processor.process_request(request_data, context)


# WebSocket connection handler
async def handle_websocket_connection(
    websocket: WebSocketServerProtocol,
    path: str,
    stream_manager: StreamManager,
    auth_handler: Optional[Callable] = None
):
    """
    Handle WebSocket connections for streaming.
    
    Args:
        websocket: WebSocket connection
        path: Connection path
        stream_manager: Stream manager instance
        auth_handler: Optional authentication handler
    """
    if not WEBSOCKETS_AVAILABLE:
        logger.error("WebSocket support not available. Install websockets package.")
        return
    
    logger.info(f"WebSocket connection established: {websocket.remote_address}")
    
    try:
        # Authenticate connection if handler provided
        if auth_handler:
            authenticated = await auth_handler(websocket, path)
            if not authenticated:
                await websocket.close(code=4001, reason="Authentication failed")
                return
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "create_stream":
                    # Create new stream with this WebSocket
                    stream_id = data.get("streamId")
                    participants = data.get("participants", [])
                    
                    connection = await stream_manager.create_stream(
                        stream_id=stream_id,
                        participants=participants,
                        websocket=websocket
                    )
                    
                    # Send confirmation
                    response = {
                        "type": "stream_created",
                        "streamId": connection.stream_id,
                        "status": connection.status.value
                    }
                    await websocket.send(json.dumps(response))
                
                elif message_type == "chunk":
                    # Process incoming chunk
                    chunk_data = data.get("chunk", {})
                    stream_id = chunk_data.get("streamId")
                    
                    if stream_id:
                        await stream_manager.receive_chunk(stream_id, chunk_data)
                
                elif message_type == "ping":
                    # Handle ping/pong for connection health
                    await websocket.send(json.dumps({"type": "pong"}))
                
                else:
                    logger.warning(f"Unknown WebSocket message type: {message_type}")
                    
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON over WebSocket")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                
    except ConnectionClosed:
        logger.info(f"WebSocket connection closed: {websocket.remote_address}")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Clean up any streams associated with this WebSocket
        for stream in stream_manager.get_active_streams():
            if stream.websocket == websocket:
                await stream_manager.close_stream(stream.stream_id, "connection_lost")


# Utility functions for streaming
def create_stream_manager() -> StreamManager:
    """Create a new stream manager instance"""
    return StreamManager()


async def create_text_stream(
    stream_manager: StreamManager,
    text: str,
    chunk_size: int = 100
) -> str:
    """
    Create a stream that sends text in chunks.
    
    Args:
        stream_manager: Stream manager instance
        text: Text to stream
        chunk_size: Size of each text chunk
        
    Returns:
        Stream ID
    """
    connection = await stream_manager.create_stream()
    stream_id = connection.stream_id
    
    # Stream text in chunks
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        is_final = i + chunk_size >= len(text)
        
        await stream_manager.send_chunk(
            stream_id=stream_id,
            data={"text": chunk},
            chunk_type="text",
            is_final=is_final
        )
        
        # Small delay between chunks
        await asyncio.sleep(0.1)
    
    return stream_id


async def create_data_stream(
    stream_manager: StreamManager,
    data_list: List[Any]
) -> str:
    """
    Create a stream that sends data items one by one.
    
    Args:
        stream_manager: Stream manager instance
        data_list: List of data items to stream
        
    Returns:
        Stream ID
    """
    connection = await stream_manager.create_stream()
    stream_id = connection.stream_id
    
    for i, item in enumerate(data_list):
        is_final = i == len(data_list) - 1
        
        await stream_manager.send_chunk(
            stream_id=stream_id,
            data=item,
            chunk_type="data",
            is_final=is_final
        )
        
        await asyncio.sleep(0.05)
    
    return stream_id
