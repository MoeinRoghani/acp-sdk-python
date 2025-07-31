"""
JSON-RPC 2.0 Core Processor

Handles JSON-RPC request/response processing for ACP communication.
Complies with JSON-RPC 2.0 specification with ACP-specific extensions.
"""

import uuid
import logging
from typing import Dict, Callable, Any, Optional, Union
from datetime import datetime

from ..models.generated import (
    JsonRpcRequest, JsonRpcResponse, JsonRpcResponse1, JsonRpcResponse2,
    RpcError, Method, Jsonrpc, MethodResult
)


logger = logging.getLogger(__name__)


class JsonRpcContext:
    """
    Context for JSON-RPC request processing.
    Contains request metadata and authentication information.
    """
    
    def __init__(
        self,
        request_id: Optional[Union[str, int]] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        scopes: Optional[list] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.scopes = scopes or []
        self.headers = headers or {}
        self.timestamp = datetime.utcnow()
        self.is_authenticated = user_id is not None
        self.correlation_id: Optional[str] = None
    
    def has_scope(self, scope: str) -> bool:
        """Check if user has required OAuth2 scope"""
        return scope in self.scopes
    
    def has_scopes(self, scopes: list) -> bool:
        """Check if user has all required OAuth2 scopes"""
        return all(scope in self.scopes for scope in scopes)


class JsonRpcError(Exception):
    """JSON-RPC error with code and optional data"""
    
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class JsonRpcProcessor:
    """
    Process JSON-RPC 2.0 requests and responses.
    
    Handles:
    - Request parsing and validation
    - Method routing to handlers
    - Response formatting
    - Error handling with proper JSON-RPC error codes
    """
    
    # Standard JSON-RPC 2.0 error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # ACP-specific error codes  
    TASK_NOT_FOUND = -40001
    TASK_ALREADY_COMPLETED = -40002
    STREAM_NOT_FOUND = -40003
    STREAM_ALREADY_CLOSED = -40004
    AGENT_NOT_AVAILABLE = -40005
    PERMISSION_DENIED = -40006
    AUTHENTICATION_FAILED = -40007
    INSUFFICIENT_SCOPE = -40008
    TOKEN_EXPIRED = -40009
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.middleware: list = []
    
    def register_handler(self, method: str, handler: Callable):
        """Register a method handler"""
        self.handlers[method] = handler
        logger.debug(f"Registered handler for method: {method}")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware for request processing"""
        self.middleware.append(middleware)
    
    async def process_request(
        self, 
        request_data: Dict[str, Any], 
        context: JsonRpcContext
    ) -> Dict[str, Any]:
        """
        Process a JSON-RPC request and return response.
        
        Args:
            request_data: Raw JSON-RPC request data
            context: Request context with auth info
            
        Returns:
            JSON-RPC response dictionary
        """
        try:
            # Parse and validate JSON-RPC request
            try:
                request = JsonRpcRequest.model_validate(request_data)
            except Exception as e:
                logger.error(f"Invalid JSON-RPC request: {e}")
                return self._create_error_response(
                    None, self.INVALID_REQUEST, 
                    f"Invalid Request: {str(e)}"
                )
            
            # Set request ID in context
            context.request_id = request.id
            
            # Check if method is supported
            method_str = request.method.value
            if method_str not in self.handlers:
                logger.error(f"Method not found: {method_str}")
                return self._create_error_response(
                    request.id, self.METHOD_NOT_FOUND,
                    f"Method not found: {method_str}"
                )
            
            # Apply middleware
            for middleware in self.middleware:
                try:
                    await middleware(request, context)
                except JsonRpcError as e:
                    return self._create_error_response(request.id, e.code, e.message, e.data)
                except Exception as e:
                    logger.error(f"Middleware error: {e}")
                    return self._create_error_response(
                        request.id, self.INTERNAL_ERROR, 
                        "Internal middleware error"
                    )
            
            # Execute method handler
            try:
                handler = self.handlers[method_str]
                result = await handler(request.params, context)
                
                # If no response expected (notification), return None
                if request.id is None:
                    return None
                
                # Create success response
                return self._create_success_response(request.id, result)
                
            except JsonRpcError as e:
                logger.warning(f"Handler error for {method_str}: {e.message}")
                return self._create_error_response(request.id, e.code, e.message, e.data)
            except Exception as e:
                logger.error(f"Internal error in {method_str}: {e}")
                return self._create_error_response(
                    request.id, self.INTERNAL_ERROR,
                    "Internal server error"
                )
                
        except Exception as e:
            logger.error(f"Unexpected error processing request: {e}")
            return self._create_error_response(
                None, self.INTERNAL_ERROR,
                "Unexpected server error"
            )
    
    def _create_success_response(
        self, 
        request_id: Union[str, int], 
        result: Any
    ) -> Dict[str, Any]:
        """Create a JSON-RPC success response"""
        
        # Validate result matches MethodResult schema
        try:
            if not isinstance(result, dict):
                # Convert simple results to message format
                validated_result = {
                    "type": "MESSAGE", 
                    "message": str(result)
                }
            else:
                validated_result = result
            
            # Create response using Pydantic model
            response = JsonRpcResponse1(
                jsonrpc=Jsonrpc.field_2_0,
                id=request_id,
                result=validated_result
            )
            
            return response.model_dump(by_alias=True)
            
        except Exception as e:
            logger.error(f"Error creating success response: {e}")
            return self._create_error_response(
                request_id, self.INTERNAL_ERROR,
                "Error formatting response"
            )
    
    def _create_error_response(
        self,
        request_id: Optional[Union[str, int]],
        code: int,
        message: str,
        data: Any = None
    ) -> Dict[str, Any]:
        """Create a JSON-RPC error response"""
        
        error = RpcError(code=code, message=message, data=data)
        
        response = JsonRpcResponse2(
            jsonrpc=Jsonrpc.field_2_0,
            id=request_id or 0,  # Use 0 for null request ID
            error=error
        )
        
        return response.model_dump(by_alias=True)
    
    def create_notification(
        self, 
        method: str, 
        params: Any = None
    ) -> Dict[str, Any]:
        """
        Create a JSON-RPC notification (request without ID).
        Used for server-initiated messages like webhooks.
        """
        try:
            method_enum = Method(method)
            request = JsonRpcRequest(
                jsonrpc=Jsonrpc.field_2_0,
                method=method_enum,
                params=params,
                id=None  # No ID = notification
            )
            return request.model_dump(by_alias=True, exclude_none=True)
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            raise JsonRpcError(
                self.INVALID_PARAMS,
                f"Invalid notification parameters: {e}"
            )


# Convenience functions for common error types
def task_not_found_error(task_id: str) -> JsonRpcError:
    """Create a task not found error"""
    return JsonRpcError(
        JsonRpcProcessor.TASK_NOT_FOUND,
        f"Task not found: {task_id}",
        {"taskId": task_id}
    )

def stream_not_found_error(stream_id: str) -> JsonRpcError:
    """Create a stream not found error"""
    return JsonRpcError(
        JsonRpcProcessor.STREAM_NOT_FOUND,
        f"Stream not found: {stream_id}",
        {"streamId": stream_id}
    )

def permission_denied_error(reason: str = "Permission denied") -> JsonRpcError:
    """Create a permission denied error"""
    return JsonRpcError(
        JsonRpcProcessor.PERMISSION_DENIED,
        reason
    )

def authentication_required_error() -> JsonRpcError:
    """Create an authentication required error"""
    return JsonRpcError(
        JsonRpcProcessor.AUTHENTICATION_FAILED,
        "Authentication required"
    )

def insufficient_scope_error(required_scopes: list) -> JsonRpcError:
    """Create an insufficient scope error"""
    return JsonRpcError(
        JsonRpcProcessor.INSUFFICIENT_SCOPE,
        f"Insufficient OAuth2 scope. Required: {', '.join(required_scopes)}",
        {"requiredScopes": required_scopes}
    )
