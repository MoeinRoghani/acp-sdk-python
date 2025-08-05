"""
ACP Validation Module

Provides validation utilities for ACP requests, responses, and data structures.
Uses Pydantic models for type-safe validation and detailed error reporting.
"""

import logging
from typing import Dict, Any, Optional, Union, Type
from pydantic import BaseModel, ValidationError

from ..models.generated import (
    JsonRpcRequest, JsonRpcResponse, RpcError,
    TasksCreateParams, TasksSendParams, TasksGetParams,
    TasksCancelParams, TasksSubscribeParams,
    StreamStartParams, StreamMessageParams, StreamEndParams,
    TaskNotificationParams, StreamChunkParams,
    TaskObject, StreamObject, Message, Part, Artifact
)
from .json_rpc import JsonRpcError, JsonRpcProcessor


logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, is_valid: bool, errors: Optional[list] = None, data: Any = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.data = data
    
    def __bool__(self):
        return self.is_valid
    
    @property
    def error_message(self) -> str:
        """Get formatted error message"""
        if not self.errors:
            return ""
        return "; ".join(str(error) for error in self.errors)


def validate_json_rpc_request(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate a JSON-RPC request structure.
    
    Args:
        data: Raw request data dictionary
        
    Returns:
        ValidationResult with parsed request or errors
    """
    try:
        request = JsonRpcRequest.model_validate(data)
        return ValidationResult(True, data=request)
    except ValidationError as e:
        logger.debug(f"JSON-RPC request validation failed: {e}")
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        return ValidationResult(False, errors=errors)
    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        return ValidationResult(False, errors=[f"Validation error: {str(e)}"])


def validate_json_rpc_response(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate a JSON-RPC response structure.
    
    Args:
        data: Raw response data dictionary
        
    Returns:
        ValidationResult with parsed response or errors
    """
    try:
        response = JsonRpcResponse.model_validate(data)
        return ValidationResult(True, data=response)
    except ValidationError as e:
        logger.debug(f"JSON-RPC response validation failed: {e}")
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        return ValidationResult(False, errors=errors)
    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        return ValidationResult(False, errors=[f"Validation error: {str(e)}"])


def validate_method_params(method: str, params: Any) -> ValidationResult:
    """
    Validate method parameters for specific ACP methods.
        
        Args:
            method: ACP method name (e.g., 'tasks.create')
        params: Parameters to validate
        
    Returns:
        ValidationResult with validated params or errors
    """
    
    # Method to parameter class mapping
    param_classes = {
        'tasks.create': TasksCreateParams,
        'tasks.send': TasksSendParams,
        'tasks.get': TasksGetParams,
        'tasks.cancel': TasksCancelParams,
        'tasks.subscribe': TasksSubscribeParams,
        'stream.start': StreamStartParams,
        'stream.message': StreamMessageParams,
        'stream.end': StreamEndParams,
        'task.notification': TaskNotificationParams,
        'stream.chunk': StreamChunkParams,
    }
    
    if method not in param_classes:
        return ValidationResult(False, errors=[f"Unknown method: {method}"])
    
    param_class = param_classes[method]
    
    try:
        if params is None:
            validated_params = param_class()
        else:
            validated_params = param_class.model_validate(params)
        return ValidationResult(True, data=validated_params)
    except ValidationError as e:
        logger.debug(f"Method params validation failed for {method}: {e}")
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        return ValidationResult(False, errors=errors)
    except Exception as e:
        logger.error(f"Unexpected validation error for {method}: {e}")
        return ValidationResult(False, errors=[f"Validation error: {str(e)}"])


def validate_message(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate an ACP message structure.
    
    Args:
        data: Message data dictionary
        
    Returns:
        ValidationResult with validated message or errors
    """
    try:
        message = Message.model_validate(data)
        return ValidationResult(True, data=message)
    except ValidationError as e:
        logger.debug(f"Message validation failed: {e}")
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        return ValidationResult(False, errors=errors)
    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        return ValidationResult(False, errors=[f"Validation error: {str(e)}"])


def validate_task_object(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate a TaskObject structure.
    
    Args:
        data: TaskObject data dictionary
        
    Returns:
        ValidationResult with validated task or errors
    """
    try:
        task = TaskObject.model_validate(data)
        return ValidationResult(True, data=task)
    except ValidationError as e:
        logger.debug(f"TaskObject validation failed: {e}")
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        return ValidationResult(False, errors=errors)
    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        return ValidationResult(False, errors=[f"Validation error: {str(e)}"])


def validate_stream_object(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate a StreamObject structure.
    
    Args:
        data: StreamObject data dictionary
        
    Returns:
        ValidationResult with validated stream or errors
    """
    try:
        stream = StreamObject.model_validate(data)
        return ValidationResult(True, data=stream)
    except ValidationError as e:
        logger.debug(f"StreamObject validation failed: {e}")
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        return ValidationResult(False, errors=errors)
    except Exception as e:
        logger.error(f"Unexpected validation error: {e}")
        return ValidationResult(False, errors=[f"Validation error: {str(e)}"])


class RequestValidator:
    """
    Middleware-style validator for ACP requests.
    Can be used as middleware in the JSON-RPC processor.
    """
    
    def __init__(self, strict: bool = True):
        """
        Args:
            strict: If True, raise errors for invalid data. 
                   If False, log warnings and continue.
        """
        self.strict = strict
    
    async def __call__(self, request: JsonRpcRequest, context) -> None:
        """
        Validate a JSON-RPC request as middleware.
        
        Args:
            request: Parsed JSON-RPC request
            context: Request context
            
        Raises:
            JsonRpcError: If validation fails and strict=True
        """
        # Validate method parameters
        if request.params is not None:
            result = validate_method_params(request.method.value, request.params)
            if not result:
                message = f"Invalid parameters for {request.method.value}: {result.error_message}"
                if self.strict:
                    raise JsonRpcError(
                        JsonRpcProcessor.INVALID_PARAMS,
                        message,
                        {"validationErrors": result.errors}
                    )
                else:
                    logger.warning(message)
        
        # Additional ACP-specific validations can be added here
        await self._validate_business_rules(request, context)
    
    async def _validate_business_rules(self, request: JsonRpcRequest, context) -> None:
        """
        Validate ACP business rules and OAuth2 enforcement.
        All operations require authentication and proper scopes.
        """
        method = request.method.value
        
        # ALL OPERATIONS REQUIRE AUTHENTICATION
        if not context.is_authenticated:
            raise JsonRpcError(
                JsonRpcProcessor.AUTHENTICATION_FAILED,
                f"Method '{method}' requires OAuth2 authentication"
            )
        
        # ALL OPERATIONS REQUIRE BASIC AGENT IDENTIFICATION SCOPE
        if not context.has_scope('acp:agent:identify'):
            raise JsonRpcError(
                JsonRpcProcessor.INSUFFICIENT_SCOPE,
                f"Method '{method}' requires 'acp:agent:identify' scope",
                {"requiredScopes": ["acp:agent:identify"]}
            )
        
        # TASK OPERATIONS SCOPE ENFORCEMENT
        if method == 'tasks.create' or method == 'tasks.send':
            if not context.has_scope('acp:tasks:write'):
                raise JsonRpcError(
                    JsonRpcProcessor.INSUFFICIENT_SCOPE,
                    f"Method '{method}' requires 'acp:tasks:write' scope",
                    {"requiredScopes": ["acp:tasks:write"]}
                )
        elif method == 'tasks.get':
            if not context.has_scope('acp:tasks:read'):
                raise JsonRpcError(
                    JsonRpcProcessor.INSUFFICIENT_SCOPE,
                    f"Method '{method}' requires 'acp:tasks:read' scope",
                    {"requiredScopes": ["acp:tasks:read"]}
                )
        elif method == 'tasks.cancel':
            if not context.has_scope('acp:tasks:cancel'):
                raise JsonRpcError(
                    JsonRpcProcessor.INSUFFICIENT_SCOPE,
                    f"Method '{method}' requires 'acp:tasks:cancel' scope",
                    {"requiredScopes": ["acp:tasks:cancel"]}
                )
        elif method == 'tasks.subscribe':
            if not context.has_scope('acp:notifications:receive'):
                raise JsonRpcError(
                    JsonRpcProcessor.INSUFFICIENT_SCOPE,
                    f"Method '{method}' requires 'acp:notifications:receive' scope",
                    {"requiredScopes": ["acp:notifications:receive"]}
                )
        
        # STREAM OPERATIONS SCOPE ENFORCEMENT
        if method == 'stream.start' or method == 'stream.message' or method == 'stream.end':
            if not context.has_scope('acp:streams:write'):
                raise JsonRpcError(
                    JsonRpcProcessor.INSUFFICIENT_SCOPE,
                    f"Method '{method}' requires 'acp:streams:write' scope",
                    {"requiredScopes": ["acp:streams:write"]}
                )
        elif method.startswith('stream.') and method not in ['stream.start', 'stream.message', 'stream.end']:
            # Other stream operations require read access
            if not context.has_scope('acp:streams:read'):
                raise JsonRpcError(
                    JsonRpcProcessor.INSUFFICIENT_SCOPE,
                    f"Method '{method}' requires 'acp:streams:read' scope",
                    {"requiredScopes": ["acp:streams:read"]}
                )


class ResponseValidator:
    """Validator for ACP responses"""
    
    @staticmethod
    def validate_response_data(data: Dict[str, Any]) -> ValidationResult:
        """
        Validate response data before sending.
        
        Args:
            data: Response data dictionary
            
        Returns:
            ValidationResult indicating if response is valid
        """
        return validate_json_rpc_response(data)


# Convenience functions for common validations
def validate_request(data: Dict[str, Any]) -> bool:
    """
    Quick validation check for JSON-RPC requests.
    
    Args:
        data: Request data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    result = validate_json_rpc_request(data)
    return result.is_valid


def validate_response(data: Dict[str, Any]) -> bool:
    """
    Quick validation check for JSON-RPC responses.
    
    Args:
        data: Response data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    result = validate_json_rpc_response(data)
    return result.is_valid


def get_validation_errors(data: Dict[str, Any], model_class: Type[BaseModel]) -> list:
    """
    Get detailed validation errors for any Pydantic model.
    
    Args:
        data: Data to validate
        model_class: Pydantic model class to validate against
        
    Returns:
        List of validation error messages
    """
    try:
        model_class.model_validate(data)
        return []
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")
        return errors
    except Exception as e:
        return [f"Validation error: {str(e)}"]
