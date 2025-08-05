"""
ACP Server Middleware

Middleware components for authentication, logging, and request processing
in the ACP server.
"""

import os
import time
import uuid
import logging
from typing import Optional, Dict, Any, List
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from ..core.json_rpc import JsonRpcContext
from ..exceptions import AuthenticationFailed, TokenExpired

logger = logging.getLogger(__name__)

# Import JWT validation for real OAuth2 support
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("PyJWT not available - install with: pip install PyJWT")

# OAuth2 configuration
ENVIRONMENT = os.getenv("ACP_ENVIRONMENT", "production").lower()

# OAuth2 Provider Configuration
OAUTH_JWKS_URL = os.getenv("OAUTH_JWKS_URL", "")
OAUTH_ISSUER = os.getenv("OAUTH_ISSUER", "")
OAUTH_AUDIENCE = os.getenv("OAUTH_AUDIENCE", "")

# OAuth2 Provider Type (auth0, google, azure, okta, custom)
OAUTH_PROVIDER = os.getenv("OAUTH_PROVIDER", "")
OAUTH_DOMAIN = os.getenv("OAUTH_DOMAIN", "")  # For auth0, okta
OAUTH_TENANT_ID = os.getenv("OAUTH_TENANT_ID", "")  # For azure

# Initialize JWT validator
jwt_validator = None

if OAUTH_PROVIDER and OAUTH_PROVIDER != "custom":
    # Use predefined provider configuration
    try:
        from ..auth.jwt_validator import OAuth2ProviderValidator
        
        provider_config = {}
        if OAUTH_DOMAIN:
            provider_config["domain"] = OAUTH_DOMAIN
        if OAUTH_TENANT_ID:
            provider_config["tenant_id"] = OAUTH_TENANT_ID
        
        jwt_validator = OAuth2ProviderValidator.create_validator(
            OAUTH_PROVIDER,
            audience=OAUTH_AUDIENCE,
            **provider_config
        )
        logger.info(f"🔐 OAuth2 validation enabled for provider: {OAUTH_PROVIDER}")
        
    except Exception as e:
        logger.error(f"Failed to initialize OAuth2 provider {OAUTH_PROVIDER}: {e}")
        
elif OAUTH_JWKS_URL and OAUTH_ISSUER:
    # Use custom OAuth2 provider configuration
    try:
        from ..auth.jwt_validator import JWTValidator
        
        jwt_validator = JWTValidator(
            jwks_url=OAUTH_JWKS_URL,
            issuer=OAUTH_ISSUER,
            audience=OAUTH_AUDIENCE
        )
        logger.info(f"🔒 Custom OAuth2 validation enabled (issuer: {OAUTH_ISSUER})")
        
    except Exception as e:
        logger.error(f"Failed to initialize custom OAuth2 validator: {e}")
        
else:
    logger.warning(f"⚠️  No OAuth2 configuration found - all requests will be rejected")
    logger.info("Set OAUTH_PROVIDER (auth0/google/azure/okta) or OAUTH_JWKS_URL + OAUTH_ISSUER")


async def extract_auth_context(request: Request) -> JsonRpcContext:
    """
    Extract authentication context from HTTP request.
    
    Parses Authorization header, validates OAuth2 token, and creates
    JsonRpcContext with user information and scopes.
    
    Args:
        request: FastAPI request object
        
    Returns:
        JsonRpcContext with authentication information
    """
    # Extract authorization header
    auth_header = request.headers.get("authorization", "")
    
    # Initialize context with basic info
    context = JsonRpcContext(
        headers=dict(request.headers),
        user_id=None,
        agent_id=None,
        scopes=[]
    )
    
    # Parse Bearer token
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Validate token and extract user info
            user_info = await validate_oauth_token(token)
            
            if user_info:
                context.user_id = user_info.get("sub")  # Subject (user ID)
                context.agent_id = user_info.get("agent_id")
                context.scopes = user_info.get("scope", "").split()
                
                logger.debug(f"Authenticated user: {context.user_id}, scopes: {context.scopes}")
            
        except TokenExpired:
            logger.warning("OAuth2 token expired")
            # Context remains unauthenticated
        except AuthenticationFailed as e:
            logger.warning(f"Authentication failed: {e}")
            # Context remains unauthenticated
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            # Context remains unauthenticated
    
    # Extract correlation ID for request tracking
    correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    context.correlation_id = correlation_id
    
    return context


async def validate_oauth_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate OAuth2 JWT token using configured OAuth2 provider.
    
    Args:
        token: OAuth2 bearer token (JWT)
        
    Returns:
        Dictionary with token claims and user information
        
    Raises:
        AuthenticationFailed: If token is invalid
        TokenExpired: If token is expired
    """
    if not token:
        raise AuthenticationFailed("No token provided")
    
    if not jwt_validator:
        logger.error("No JWT validator configured")
        raise AuthenticationFailed("OAuth2 authentication not configured")
    
    try:
        # Validate JWT token using configured provider
        payload = await jwt_validator.validate_token(token)
        
        # Extract scope information (different providers use different claim names)
        scopes = []
        for scope_claim in ["scope", "scp", "permissions"]:
            if scope_claim in payload:
                scope_value = payload[scope_claim]
                if isinstance(scope_value, str):
                    scopes = scope_value.split()
                elif isinstance(scope_value, list):
                    scopes = scope_value
                break
        
        # Normalize payload for ACP context
        user_info = {
            "sub": payload.get("sub"),  # Subject (user ID)
            "iss": payload.get("iss"),  # Issuer
            "aud": payload.get("aud"),  # Audience
            "exp": payload.get("exp"),  # Expiration time
            "iat": payload.get("iat"),  # Issued at
            "scope": " ".join(scopes) if scopes else "",
            "agent_id": payload.get("agent_id", payload.get("azp", payload.get("client_id"))),  # Agent/client ID
            "_provider": payload.get("_acp_provider", "unknown")
        }
        
        # Add any additional claims
        for key, value in payload.items():
            if key not in user_info and not key.startswith("_"):
                user_info[key] = value
        
        logger.debug(f"🔐 OAuth2 authenticated user: {user_info.get('sub')} with scopes: {user_info.get('scope')}")
        return user_info
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise TokenExpired("JWT token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT token validation failed: {e}")
        raise AuthenticationFailed(f"Invalid JWT token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error validating JWT token: {e}")
        raise AuthenticationFailed(f"Token validation error: {str(e)}")


async def logging_middleware(request: Request, call_next):
    """
    Logging middleware for request/response tracking.
    
    Logs request details, timing, and response status for monitoring
    and debugging purposes.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
        
    Returns:
        Response from downstream handler
    """
    # Generate correlation ID for request tracking
    correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    
    # Start timing
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        f"[{correlation_id}] {request.method} {request.url.path} - "
        f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
    )
    
    # Add correlation ID to response headers
    response = None
    try:
        response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        
    except Exception as e:
        # Log error and re-raise
        duration = time.time() - start_time
        logger.error(
            f"[{correlation_id}] Request failed after {duration:.3f}s: {e}"
        )
        raise
    
    # Log response
    duration = time.time() - start_time
    logger.info(
        f"[{correlation_id}] {response.status_code} - {duration:.3f}s"
    )
    
    return response


async def cors_middleware(request: Request, call_next):
    """
    CORS middleware for handling cross-origin requests.
    
    Note: This is redundant if using FastAPI's CORSMiddleware,
    but provides custom CORS logic if needed.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
        
    Returns:
        Response with CORS headers
    """
    # Handle preflight requests
    if request.method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "Authorization, Content-Type",
                "Access-Control-Max-Age": "86400",
            }
        )
    
    # Process request
    response = await call_next(request)
    
    # Add CORS headers to response
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response


class RateLimitMiddleware:
    """
    Rate limiting middleware to prevent abuse.
    
    Implements token bucket algorithm for rate limiting
    based on client IP or user ID.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        key_func: callable = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Sustained request rate limit
            burst_size: Maximum burst size
            key_func: Function to extract rate limit key from request
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.key_func = key_func or self._default_key_func
        self.buckets: Dict[str, Dict] = {}
    
    def _default_key_func(self, request: Request) -> str:
        """Default key function using client IP"""
        return request.client.host if request.client else "unknown"
    
    async def __call__(self, request: Request, call_next):
        """
        Process request with rate limiting.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
            
        Returns:
            Response or rate limit error
        """
        key = self.key_func(request)
        
        # Check rate limit
        if not self._check_rate_limit(key):
            logger.warning(f"Rate limit exceeded for key: {key}")
            return JSONResponse(
                status_code=429,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32003,  # Custom rate limit error
                        "message": "Rate limit exceeded"
                    },
                    "id": None
                }
            )
        
        return await call_next(request)
    
    def _check_rate_limit(self, key: str) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key
            
        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        
        # Initialize bucket if not exists
        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": self.burst_size,
                "last_update": now
            }
        
        bucket = self.buckets[key]
        
        # Calculate tokens to add based on time elapsed
        time_passed = now - bucket["last_update"]
        tokens_to_add = time_passed * (self.requests_per_minute / 60.0)
        
        # Update bucket
        bucket["tokens"] = min(
            self.burst_size,
            bucket["tokens"] + tokens_to_add
        )
        bucket["last_update"] = now
        
        # Check if request can be processed
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        
        return False


class RequestValidationMiddleware:
    """
    Request validation middleware for additional security checks.
    """
    
    def __init__(
        self,
        max_request_size: int = 1024 * 1024,  # 1MB
        allowed_content_types: List[str] = None
    ):
        """
        Initialize validation middleware.
        
        Args:
            max_request_size: Maximum request body size in bytes
            allowed_content_types: List of allowed content types
        """
        self.max_request_size = max_request_size
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/json-rpc"
        ]
    
    async def __call__(self, request: Request, call_next):
        """
        Validate request before processing.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
            
        Returns:
            Response or validation error
        """
        # Check content type for POST requests
        if request.method == "POST":
            content_type = request.headers.get("content-type", "").split(";")[0]
            if content_type not in self.allowed_content_types:
                return JSONResponse(
                    status_code=415,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": f"Unsupported content type: {content_type}"
                        },
                        "id": None
                    }
                )
        
        # Note: Request size validation would need to be implemented
        # at the FastAPI level or using a custom body parser
        
        return await call_next(request)


# Utility functions for middleware configuration

def create_rate_limit_middleware(
    requests_per_minute: int = 60,
    burst_size: int = 10
) -> RateLimitMiddleware:
    """
    Create configured rate limit middleware.
    
    Args:
        requests_per_minute: Sustained request rate
        burst_size: Maximum burst size
        
    Returns:
        Configured RateLimitMiddleware instance
    """
    return RateLimitMiddleware(requests_per_minute, burst_size)


def create_validation_middleware(
    max_request_size: int = 1024 * 1024
) -> RequestValidationMiddleware:
    """
    Create configured validation middleware.
    
    Args:
        max_request_size: Maximum request size in bytes
        
    Returns:
        Configured RequestValidationMiddleware instance
    """
    return RequestValidationMiddleware(max_request_size)
