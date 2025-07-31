"""
ACP Exception Classes

Consolidated exception hierarchy for the ACP Python SDK.
Contains standard exceptions for JSON-RPC errors, authentication failures,
network issues, and ACP-specific business logic errors.
"""


class ACPException(Exception):
    """
    Base exception for all ACP-related errors.
    
    Provides common functionality for error tracking and debugging.
    """
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self):
        """Convert exception to dictionary format"""
        return {
            "error": self.__class__.__name__,
            "message": str(self),
            "error_code": self.error_code,
            "details": self.details
        }


# === Core JSON-RPC Errors ===

class JsonRpcError(ACPException):
    """
    JSON-RPC 2.0 protocol error.
    
    Represents errors in the JSON-RPC protocol itself, not business logic errors.
    These errors have standard codes as defined in the JSON-RPC 2.0 specification.
    """
    
    def __init__(self, code: int, message: str, data=None):
        super().__init__(message)
        self.code = code
        self.data = data


class ParseError(JsonRpcError):
    """JSON could not be parsed"""
    def __init__(self, message: str = "Parse error"):
        super().__init__(-32700, message)


class InvalidRequest(JsonRpcError):
    """JSON-RPC request is invalid"""
    def __init__(self, message: str = "Invalid Request"):
        super().__init__(-32600, message)


class MethodNotFound(JsonRpcError):
    """Method does not exist or is not available"""
    def __init__(self, method: str):
        super().__init__(-32601, f"Method not found: {method}")


class InvalidParams(JsonRpcError):
    """Invalid method parameters"""
    def __init__(self, message: str = "Invalid params"):
        super().__init__(-32602, message)


class InternalError(JsonRpcError):
    """Internal JSON-RPC error"""
    def __init__(self, message: str = "Internal error"):
        super().__init__(-32603, message)


# === ACP-Specific Errors ===

class TaskNotFound(ACPException):
    """
    Task with the specified ID was not found.
    
    This typically happens when:
    - Task ID is incorrect
    - Task was deleted
    - User doesn't have access to the task
    """
    def __init__(self, task_id: str):
        super().__init__(f"Task not found: {task_id}", "TASK_NOT_FOUND", {"taskId": task_id})


class TaskAlreadyCompleted(ACPException):
    """
    Operation cannot be performed because task is already completed.
    
    This happens when trying to:
    - Send messages to completed tasks
    - Cancel completed tasks
    - Modify completed task state
    """
    def __init__(self, task_id: str, status: str):
        super().__init__(
            f"Task {task_id} is already {status}",
            "TASK_ALREADY_COMPLETED",
            {"taskId": task_id, "status": status}
        )


class StreamNotFound(ACPException):
    """
    Stream with the specified ID was not found.
    
    This typically happens when:
    - Stream ID is incorrect
    - Stream was closed/deleted
    - User doesn't have access to the stream
    """
    def __init__(self, stream_id: str):
        super().__init__(f"Stream not found: {stream_id}", "STREAM_NOT_FOUND", {"streamId": stream_id})


class StreamAlreadyClosed(ACPException):
    """
    Operation cannot be performed because stream is already closed.
    """
    def __init__(self, stream_id: str):
        super().__init__(f"Stream {stream_id} is already closed", "STREAM_ALREADY_CLOSED", {"streamId": stream_id})


class AgentNotAvailable(ACPException):
    """
    Target agent is not available or cannot be reached.
    """
    def __init__(self, agent_id: str, reason: str = None):
        message = f"Agent not available: {agent_id}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "AGENT_NOT_AVAILABLE", {"agentId": agent_id, "reason": reason})


class PermissionDenied(ACPException):
    """User does not have permission to perform the requested operation."""
    def __init__(self, resource: str = None, action: str = None):
        if resource and action:
            message = f"Permission denied for {action} on {resource}"
        else:
            message = "Permission denied"
        super().__init__(message, "PERMISSION_DENIED", {"resource": resource, "action": action})


class AuthenticationFailed(ACPException):
    """Authentication failed or token is invalid."""
    def __init__(self, reason: str = "Authentication failed"):
        super().__init__(reason, "AUTHENTICATION_FAILED")


class InsufficientScope(ACPException):
    """
    OAuth2 token does not have sufficient scope for the requested operation.
    """
    def __init__(self, required_scopes: list, provided_scopes: list = None):
        message = f"Insufficient OAuth2 scope. Required: {', '.join(required_scopes)}"
        super().__init__(
            message, 
            "INSUFFICIENT_SCOPE",
            {"requiredScopes": required_scopes, "providedScopes": provided_scopes}
        )


class TokenExpired(ACPException):
    """
    OAuth2 access token has expired and needs to be refreshed.
    """
    def __init__(self, token_type: str = "access_token"):
        super().__init__(f"{token_type} has expired", "TOKEN_EXPIRED", {"tokenType": token_type})


# === Network and Communication Errors ===

class ClientError(ACPException):
    """
    Client-side error occurred during communication.
    
    These are typically 4xx HTTP errors or client configuration issues.
    """
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message, "CLIENT_ERROR", {"statusCode": status_code, "responseData": response_data})
        self.status_code = status_code
        self.response_data = response_data


class NetworkError(ClientError):
    """Network communication failed"""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message, error_code="NETWORK_ERROR")
        self.original_error = original_error


class TimeoutError(NetworkError):
    """Request timed out"""
    def __init__(self, timeout_seconds: float):
        super().__init__(f"Request timed out after {timeout_seconds} seconds", error_code="TIMEOUT")
        self.timeout_seconds = timeout_seconds


class ConnectionError(NetworkError):
    """Could not establish connection to target agent"""
    def __init__(self, url: str, original_error: Exception = None):
        super().__init__(f"Could not connect to {url}", original_error)
        self.url = url


# === Validation Errors ===

class ValidationError(ACPException):
    """
    Request validation failed.
    
    This happens when:
    - Required fields are missing
    - Field values are invalid
    - Schema validation fails
    """
    def __init__(self, message: str, field: str = None, value=None, errors: list = None):
        super().__init__(
            message,
            "VALIDATION_ERROR",
            {"field": field, "value": value, "errors": errors}
        )
        self.field = field
        self.value = value
        self.errors = errors or []


class SchemaValidationError(ValidationError):
    """Pydantic schema validation failed"""
    def __init__(self, pydantic_error, schema_name: str = None):
        errors = []
        if hasattr(pydantic_error, 'errors'):
            errors = pydantic_error.errors()
        
        message = f"Schema validation failed for {schema_name or 'unknown schema'}"
        super().__init__(message, errors=errors)
        self.pydantic_error = pydantic_error


# === Server Errors ===

class ServerError(ACPException):
    """
    Server-side error occurred during processing.
    
    These are typically 5xx HTTP errors or server internal issues.
    """
    def __init__(self, message: str, status_code: int = 500, error_data: dict = None):
        super().__init__(message, "SERVER_ERROR", {"statusCode": status_code, "errorData": error_data})
        self.status_code = status_code
        self.error_data = error_data


class InternalServerError(ServerError):
    """Internal server error (500)"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, 500)


class ServiceUnavailable(ServerError):
    """Service temporarily unavailable (503)"""
    def __init__(self, message: str = "Service unavailable", retry_after: int = None):
        super().__init__(message, 503, {"retryAfter": retry_after})
        self.retry_after = retry_after


class BadGateway(ServerError):
    """Bad gateway error (502)"""
    def __init__(self, upstream_service: str = None):
        message = f"Bad gateway: {upstream_service}" if upstream_service else "Bad gateway"
        super().__init__(message, 502, {"upstreamService": upstream_service})


# === Agent-Specific Errors ===

class AgentError(ACPException):
    """
    Agent-specific business logic error.
    
    These are errors specific to the agent's domain or functionality.
    """
    def __init__(self, message: str, agent_error_code: str = None, context: dict = None):
        super().__init__(message, f"AGENT_{agent_error_code}" if agent_error_code else "AGENT_ERROR", context)
        self.agent_error_code = agent_error_code
        self.context = context or {}


class AgentBusy(AgentError):
    """Agent is too busy to process the request"""
    def __init__(self, estimated_wait_time: int = None):
        message = "Agent is busy"
        if estimated_wait_time:
            message += f". Estimated wait time: {estimated_wait_time} seconds"
        
        super().__init__(
            message,
            "BUSY",
            {"estimatedWaitTime": estimated_wait_time}
        )


class AgentCapabilityNotSupported(AgentError):
    """Agent does not support the requested capability"""
    def __init__(self, capability: str, supported_capabilities: list = None):
        message = f"Capability not supported: {capability}"
        super().__init__(
            message,
            "CAPABILITY_NOT_SUPPORTED",
            {"capability": capability, "supportedCapabilities": supported_capabilities}
        )


# === Utility Functions ===

def get_error_hierarchy():
    """
    Get the complete ACP exception hierarchy as a dictionary.
    
    Useful for documentation generation and error handling logic.
    """
    return {
        "ACPException": {
            "JsonRpcError": ["ParseError", "InvalidRequest", "MethodNotFound", "InvalidParams", "InternalError"],
            "TaskNotFound": [],
            "TaskAlreadyCompleted": [],
            "StreamNotFound": [],
            "StreamAlreadyClosed": [],
            "AgentNotAvailable": [],
            "PermissionDenied": [],
            "AuthenticationFailed": [],
            "InsufficientScope": [],
            "TokenExpired": [],
            "ClientError": ["NetworkError", "TimeoutError", "ConnectionError"],
            "ValidationError": ["SchemaValidationError"],
            "ServerError": ["InternalServerError", "ServiceUnavailable", "BadGateway"],
            "AgentError": ["AgentBusy", "AgentCapabilityNotSupported"]
        }
    }


def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an error is potentially retryable.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if the error might succeed on retry, False otherwise
    """
    # Network errors are generally retryable
    if isinstance(exception, (NetworkError, TimeoutError, ConnectionError)):
        return True
    
    # Server errors might be retryable
    if isinstance(exception, (ServiceUnavailable, BadGateway)):
        return True
    
    # Agent busy is retryable
    if isinstance(exception, AgentBusy):
        return True
    
    # Authentication and permission errors are not retryable
    if isinstance(exception, (AuthenticationFailed, PermissionDenied, InsufficientScope)):
        return False
    
    # Validation errors are not retryable
    if isinstance(exception, ValidationError):
        return False
    
    # Task/stream not found errors are not retryable
    if isinstance(exception, (TaskNotFound, StreamNotFound)):
        return False
    
    # Default to not retryable for safety
    return False
