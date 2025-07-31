"""
ACP Server Decorators

Decorators for ACP method handlers that provide authentication,
validation, rate limiting, and other cross-cutting concerns.
"""

import logging
import functools
from typing import Callable, List, Optional, Type, Any, Dict
from datetime import datetime

from ..core.json_rpc import JsonRpcError, JsonRpcContext, JsonRpcProcessor
from ..core.validation import validate_method_params, ValidationResult
from ..exceptions import (
    AuthenticationFailed, PermissionDenied, InsufficientScope,
    ValidationError
)
from ..models.generated import TasksCreateParams, StreamStartParams  # Import other param types as needed


logger = logging.getLogger(__name__)


def require_auth(scopes: Optional[List[str]] = None):
    """
    Decorator to require authentication for a method handler.
    
    Args:
        scopes: List of required OAuth2 scopes
        
    Example:
        @require_auth(["acp:tasks:write"])
        async def handle_task_create(params, context):
            return {"taskId": "123", "status": "SUBMITTED"}
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(params, context: JsonRpcContext, *args, **kwargs):
            # Check authentication
            if not context.is_authenticated:
                raise JsonRpcError(
                    JsonRpcProcessor.AUTHENTICATION_FAILED,
                    "Authentication required"
                )
            
            # Check scopes if specified
            if scopes and not context.has_scopes(scopes):
                raise JsonRpcError(
                    JsonRpcProcessor.INSUFFICIENT_SCOPE,
                    f"Insufficient OAuth2 scope. Required: {', '.join(scopes)}",
                    {"requiredScopes": scopes}
                )
            
            return await func(params, context, *args, **kwargs)
        
        return wrapper
    return decorator


def validate_params(param_class: Type):
    """
    Decorator to validate method parameters using Pydantic models.
    
    Args:
        param_class: Pydantic model class for parameter validation
        
    Example:
        @validate_params(TasksCreateParams)
        async def handle_task_create(params: TasksCreateParams, context):
            return {"taskId": "123", "status": "SUBMITTED"}
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(params, context: JsonRpcContext, *args, **kwargs):
            # Validate parameters
            if params is not None:
                try:
                    validated_params = param_class.model_validate(params)
                    return await func(validated_params, context, *args, **kwargs)
                except Exception as e:
                    raise JsonRpcError(
                        JsonRpcProcessor.INVALID_PARAMS,
                        f"Invalid parameters: {str(e)}"
                    )
            else:
                # Handle case where params is None but validation is required
                try:
                    validated_params = param_class()
                    return await func(validated_params, context, *args, **kwargs)
                except Exception as e:
                    raise JsonRpcError(
                        JsonRpcProcessor.INVALID_PARAMS,
                        f"Parameters required: {str(e)}"
                    )
        
        return wrapper
    return decorator


def rate_limit(
    requests_per_minute: int = 60,
    per_user: bool = True,
    burst_size: int = 10
):
    """
    Decorator to add rate limiting to method handlers.
    
    Args:
        requests_per_minute: Number of requests allowed per minute
        per_user: If True, limit per user; if False, limit globally
        burst_size: Maximum burst size
        
    Example:
        @rate_limit(requests_per_minute=30, per_user=True)
        async def handle_expensive_operation(params, context):
            return {"result": "success"}
    """
    def decorator(func: Callable):
        # Initialize rate limit storage
        if not hasattr(func, '_rate_limit_buckets'):
            func._rate_limit_buckets = {}
        
        @functools.wraps(func)
        async def wrapper(params, context: JsonRpcContext, *args, **kwargs):
            import time
            
            # Determine rate limit key
            if per_user and context.user_id:
                key = f"user:{context.user_id}"
            elif per_user:
                key = f"ip:{getattr(context, 'client_ip', 'unknown')}"
            else:
                key = "global"
            
            now = time.time()
            
            # Initialize bucket if not exists
            if key not in func._rate_limit_buckets:
                func._rate_limit_buckets[key] = {
                    "tokens": burst_size,
                    "last_update": now
                }
            
            bucket = func._rate_limit_buckets[key]
            
            # Calculate tokens to add
            time_passed = now - bucket["last_update"]
            tokens_to_add = time_passed * (requests_per_minute / 60.0)
            
            # Update bucket
            bucket["tokens"] = min(burst_size, bucket["tokens"] + tokens_to_add)
            bucket["last_update"] = now
            
            # Check if request can be processed
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return await func(params, context, *args, **kwargs)
            else:
                logger.warning(f"Rate limit exceeded for key: {key}")
                raise JsonRpcError(
                    -32003,  # Custom rate limit error code
                    "Rate limit exceeded",
                    {
                        "retryAfter": 60 / requests_per_minute,
                        "limit": requests_per_minute
                    }
                )
        
        return wrapper
    return decorator


def log_method_calls(
    log_params: bool = False,
    log_result: bool = False,
    log_level: str = "INFO"
):
    """
    Decorator to log method calls for debugging and monitoring.
    
    Args:
        log_params: Whether to log method parameters
        log_result: Whether to log method result  
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Example:
        @log_method_calls(log_params=True, log_result=True)
        async def handle_task_create(params, context):
            return {"taskId": "123", "status": "SUBMITTED"}
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(params, context: JsonRpcContext, *args, **kwargs):
            import time
            
            correlation_id = getattr(context, 'correlation_id', 'unknown')
            user_id = context.user_id or 'anonymous'
            
            # Log method call start
            log_message = f"[{correlation_id}] {func.__name__} called by {user_id}"
            if log_params:
                log_message += f" with params: {params}"
            
            getattr(logger, log_level.lower())(log_message)
            
            start_time = time.time()
            
            try:
                # Execute method
                result = await func(params, context, *args, **kwargs)
                
                # Log successful completion
                duration = time.time() - start_time
                log_message = f"[{correlation_id}] {func.__name__} completed in {duration:.3f}s"
                if log_result:
                    log_message += f" with result: {result}"
                
                getattr(logger, log_level.lower())(log_message)
                
                return result
                
            except Exception as e:
                # Log error
                duration = time.time() - start_time
                logger.error(
                    f"[{correlation_id}] {func.__name__} failed after {duration:.3f}s: {e}"
                )
                raise
        
        return wrapper
    return decorator


def cache_result(
    ttl_seconds: int = 300,
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache method results for performance.
    
    Args:
        ttl_seconds: Time to live for cached results
        key_func: Function to generate cache key from params and context
        
    Example:
        @cache_result(ttl_seconds=600)
        async def handle_expensive_query(params, context):
            return {"result": "expensive_computation()"}
    """
    def decorator(func: Callable):
        # Initialize cache storage
        if not hasattr(func, '_cache'):
            func._cache = {}
        
        @functools.wraps(func)
        async def wrapper(params, context: JsonRpcContext, *args, **kwargs):
            import time
            import hashlib
            import json
            
            # Generate cache key
            if key_func:
                cache_key = key_func(params, context)
            else:
                # Default key generation
                key_data = {
                    "method": func.__name__,
                    "params": params,
                    "user_id": context.user_id
                }
                key_str = json.dumps(key_data, sort_keys=True, default=str)
                cache_key = hashlib.md5(key_str.encode()).hexdigest()
            
            now = time.time()
            
            # Check cache
            if cache_key in func._cache:
                cached_result, timestamp = func._cache[cache_key]
                if now - timestamp < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__} with key {cache_key}")
                    return cached_result
                else:
                    # Cache expired
                    del func._cache[cache_key]
            
            # Execute method and cache result
            result = await func(params, context, *args, **kwargs)
            func._cache[cache_key] = (result, now)
            
            logger.debug(f"Cached result for {func.__name__} with key {cache_key}")
            return result
        
        return wrapper
    return decorator


def timeout(seconds: float):
    """
    Decorator to add timeout to method handlers.
    
    Args:
        seconds: Timeout in seconds
        
    Example:
        @timeout(30.0)
        async def handle_long_running_task(params, context):
            return await some_long_operation()
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(params, context: JsonRpcContext, *args, **kwargs):
            import asyncio
            
            try:
                result = await asyncio.wait_for(
                    func(params, context, *args, **kwargs),
                    timeout=seconds
                )
                return result
            except asyncio.TimeoutError:
                logger.warning(f"Method {func.__name__} timed out after {seconds}s")
                raise JsonRpcError(
                    JsonRpcProcessor.INTERNAL_ERROR,
                    f"Method timed out after {seconds} seconds"
                )
        
        return wrapper
    return decorator


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0
):
    """
    Decorator to retry method execution on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay_seconds: Initial delay between retries
        backoff_factor: Multiplier for delay on each retry
        
    Example:
        @retry(max_attempts=3, delay_seconds=1.0)
        async def handle_unreliable_operation(params, context):
            return await external_api_call()
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(params, context: JsonRpcContext, *args, **kwargs):
            import asyncio
            
            last_exception = None
            delay = delay_seconds
            
            for attempt in range(max_attempts):
                try:
                    return await func(params, context, *args, **kwargs)
                except JsonRpcError:
                    # Don't retry JSON-RPC errors (client errors)
                    raise
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # All attempts failed
            raise JsonRpcError(
                JsonRpcProcessor.INTERNAL_ERROR,
                f"Method failed after {max_attempts} attempts: {str(last_exception)}"
            )
        
        return wrapper
    return decorator


# Convenience decorators for common ACP patterns

def task_method(
    require_scopes: Optional[List[str]] = None,
    validate: bool = True,
    log_calls: bool = True
):
    """
    Composite decorator for task-related methods.
    
    Args:
        require_scopes: Required OAuth2 scopes
        validate: Whether to validate parameters
        log_calls: Whether to log method calls
        
    Example:
        @task_method(require_scopes=["acp:tasks:write"])
        async def handle_task_create(params: TasksCreateParams, context):
            return {"taskId": "123", "status": "SUBMITTED"}
    """
    def decorator(func: Callable):
        # Apply decorators in reverse order (inside-out)
        decorated_func = func
        
        if log_calls:
            decorated_func = log_method_calls()(decorated_func)
        
        if validate:
            # Auto-detect parameter type from function signature
            import inspect
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            if len(param_names) >= 1:
                param_annotation = sig.parameters[param_names[0]].annotation
                if param_annotation != inspect.Parameter.empty:
                    decorated_func = validate_params(param_annotation)(decorated_func)
        
        if require_scopes:
            decorated_func = require_auth(require_scopes)(decorated_func)
        
        return decorated_func
    
    return decorator


def stream_method(
    require_scopes: Optional[List[str]] = None,
    validate: bool = True,
    log_calls: bool = True
):
    """
    Composite decorator for stream-related methods.
    
    Args:
        require_scopes: Required OAuth2 scopes
        validate: Whether to validate parameters
        log_calls: Whether to log method calls
        
    Example:
        @stream_method(require_scopes=["acp:streams:write"])
        async def handle_stream_start(params: StreamStartParams, context):
            return {"streamId": "stream-123", "status": "ACTIVE"}
    """
    def decorator(func: Callable):
        # Apply decorators in reverse order (inside-out)
        decorated_func = func
        
        if log_calls:
            decorated_func = log_method_calls()(decorated_func)
        
        if validate:
            # Auto-detect parameter type from function signature
            import inspect
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            if len(param_names) >= 1:
                param_annotation = sig.parameters[param_names[0]].annotation
                if param_annotation != inspect.Parameter.empty:
                    decorated_func = validate_params(param_annotation)(decorated_func)
        
        if require_scopes:
            decorated_func = require_auth(require_scopes)(decorated_func)
        
        return decorated_func
    
    return decorator
