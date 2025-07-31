"""
Agent Communication Protocol (ACP) - Python Implementation

The industry-standard protocol for secure, scalable agent-to-agent communication.
Built on JSON-RPC 2.0, ACP enables AI agents to discover, authenticate, and collaborate.

Homepage: https://acp-protocol.org
Documentation: https://docs.acp-protocol.org
"""

__version__ = "1.0.0"
__author__ = "Moein Roghani"
__email__ = "moein.roghani@proton.me"
__license__ = "MIT"

# Clean, simple API - the main classes developers use
from .client.acp_client import ACPClient as Client
from .server.acp_server import ACPServer as Server

# Generated models from ACP specification
from .models.generated import (
    # JSON-RPC Foundation
    JsonRpcRequest, JsonRpcResponse, RpcError, Jsonrpc, Method,
    
    # Request Parameters
    TasksCreateParams, TasksSendParams, TasksGetParams,
    TasksCancelParams, TasksSubscribeParams,
    StreamStartParams, StreamMessageParams, StreamEndParams,
    TaskNotificationParams, StreamChunkParams,
    
    # Response Types
    MethodResult,
    
    # Core Data Models
    Message, Part, TaskObject, StreamObject, Artifact,
    Status, Priority, Event
)

# Core utilities for advanced users
from .core.json_rpc import (
    JsonRpcProcessor, JsonRpcContext, JsonRpcError,
    task_not_found_error, stream_not_found_error,
    permission_denied_error, authentication_required_error,
    insufficient_scope_error
)

from .core.validation import (
    validate_request, validate_response, ValidationResult,
    validate_json_rpc_request, validate_json_rpc_response,
    validate_method_params, validate_message,
    validate_task_object, validate_stream_object,
    RequestValidator, ResponseValidator
)

# Authentication utilities
from .client.auth import OAuth2Handler

# Essential exports for clean API
__all__ = [
    # Main API - what most developers need
    "Client",           # acp.Client (clean name)
    "Server",           # acp.Server (clean name)
    
    # Request/Response Models
    "TasksCreateParams", "TasksSendParams", "TasksGetParams",
    "TasksCancelParams", "TasksSubscribeParams",
    "StreamStartParams", "StreamMessageParams", "StreamEndParams",
    "TaskNotificationParams", "StreamChunkParams",
    "MethodResult",
    
    # Core Data Types
    "Message", "Part", "TaskObject", "StreamObject", "Artifact",
    "Status", "Priority", "Event",
    
    # JSON-RPC Foundation (for advanced users)
    "JsonRpcRequest", "JsonRpcResponse", "RpcError", "Jsonrpc", "Method",
    
    # Core Processing (for advanced users)
    "JsonRpcProcessor", "JsonRpcContext", "JsonRpcError",
    
    # Error Helpers
    "task_not_found_error", "stream_not_found_error",
    "permission_denied_error", "authentication_required_error",
    "insufficient_scope_error",
    
    # Validation
    "validate_request", "validate_response", "ValidationResult",
    "validate_json_rpc_request", "validate_json_rpc_response",
    "validate_method_params", "validate_message",
    "validate_task_object", "validate_stream_object",
    "RequestValidator", "ResponseValidator",
    
    # Authentication
    "OAuth2Handler",
] 

# Package metadata
__doc__ = """
Agent Communication Protocol (ACP) - Python Implementation

ACP is the industry-standard protocol for secure, scalable agent-to-agent 
communication. This package provides a complete Python implementation with
both client and server capabilities.

Key Features:
- JSON-RPC 2.0 compliant communication
- OAuth2 authentication and authorization
- Real-time streaming support
- Agent discovery via agent cards
- Production-ready with comprehensive validation

Quick Start:

    # Client usage
    import acp
    client = acp.Client("https://agent.example.com/jsonrpc")
    response = await client.tasks.create(params)
    
    # Server usage  
    import acp
    server = acp.Server("My Agent", "Agent description")
    
    @server.method_handler("tasks.create")
    async def handle_task(params, context):
        return {"type": "task", "task": {...}}
    
    server.run()

For more information:
- Documentation: https://docs.acp-protocol.org
- Protocol Spec: https://acp-protocol.org/spec
- Examples: https://github.com/acp-protocol/acp-python/tree/main/examples
""" 