"""
ACP Server Implementation

FastAPI-based server for handling ACP JSON-RPC requests.
Integrates with the JSON-RPC processor and provides authentication,
validation, and error handling.
"""

import logging
from typing import Dict, Callable, Optional, Any
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ..core.json_rpc import JsonRpcProcessor, JsonRpcContext, JsonRpcError
from ..core.validation import RequestValidator
from ..exceptions import ACPException, AuthenticationFailed, PermissionDenied
from .middleware import extract_auth_context, cors_middleware, logging_middleware


logger = logging.getLogger(__name__)


class ACPServer:
    """
    Server for handling incoming ACP requests using FastAPI and JSON-RPC 2.0.
    
    Features:
    - JSON-RPC 2.0 compliant request/response handling
    - OAuth2 authentication with scope validation
    - Request/response validation
    - Error handling with proper HTTP status codes
    - CORS support for web clients
    - Structured logging with correlation IDs
    """
    
    def __init__(
        self, 
        agent_name: str,
        enable_cors: bool = True,
        enable_validation: bool = True,
        enable_logging: bool = True
    ):
        """
        Initialize ACP server.
        
        Args:
            agent_name: Name of the agent (used for logging and identification)
            enable_cors: Enable CORS middleware for web clients
            enable_validation: Enable request validation middleware
            enable_logging: Enable request logging middleware
        """
        self.agent_name = agent_name
        self.app = FastAPI(
            title=f"{agent_name} ACP Server",
            description=f"Agent Communication Protocol server for {agent_name}",
            version="1.0.0"
        )
        
        # JSON-RPC processor
        self.processor = JsonRpcProcessor()
        self.handlers: Dict[str, Callable] = {}
        
        # Add middleware
        if enable_cors:
            self._add_cors_middleware()
        if enable_logging:
            self._add_logging_middleware()
        if enable_validation:
            self._add_validation_middleware()
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"ACP Server initialized for agent: {agent_name}")
    
    def _add_cors_middleware(self):
        """Add CORS middleware for web client support"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["*"],
        )
    
    def _add_logging_middleware(self):
        """Add logging middleware"""
        self.app.middleware("http")(logging_middleware)
    
    def _add_validation_middleware(self):
        """Add validation middleware to JSON-RPC processor"""
        validator = RequestValidator(strict=True)
        self.processor.add_middleware(validator)
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/jsonrpc")
        async def handle_jsonrpc(request: Request):
            """
            Main JSON-RPC endpoint for ACP communication.
            
            Handles all ACP methods according to JSON-RPC 2.0 specification.
            """
            try:
                # Parse JSON request body
                try:
                    data = await request.json()
                except Exception as e:
                    logger.error(f"Failed to parse JSON: {e}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32700,
                                "message": "Parse error"
                            },
                            "id": None
                        }
                    )
                
                # Extract authentication context
                context = await extract_auth_context(request)
                
                # Process JSON-RPC request
                response = await self.processor.process_request(data, context)
                
                # Handle notifications (no response expected)
                if response is None:
                    return JSONResponse(status_code=204, content=None)
                
                # Determine HTTP status code based on response
                http_status = 200
                if "error" in response:
                    error_code = response["error"].get("code", 0)
                    if error_code == -40007:  # Authentication failed
                        http_status = 401
                    elif error_code == -40006:  # Permission denied
                        http_status = 403
                    elif error_code in [-40001, -40003]:  # Not found errors
                        http_status = 404
                    elif -32700 <= error_code <= -32600:  # Client errors
                        http_status = 400
                    else:  # Server errors
                        http_status = 500
                
                return JSONResponse(status_code=http_status, content=response)
                
            except Exception as e:
                logger.error(f"Unexpected error in JSON-RPC handler: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": "Internal error"
                        },
                        "id": None
                    }
                )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "agent": self.agent_name}
        
        @self.app.get("/.well-known/agent.json")
        async def agent_card():
            """
            Agent discovery endpoint.
            Returns agent capabilities and metadata.
            """
            # This will be implemented when we do agent_card.py
            return {
                "name": self.agent_name,
                "version": "1.0.0",
                "url": f"/jsonrpc",
                "methods": list(self.handlers.keys()),
                "capabilities": {
                    "streaming": True,
                    "notifications": True
                }
            }
    
    def register_handler(self, method: str, handler: Callable):
        """
        Register a method handler.
        
        Args:
            method: ACP method name (e.g., 'tasks.create')
            handler: Async function to handle the method
        """
        self.processor.register_handler(method, handler)
        self.handlers[method] = handler
        logger.info(f"Registered handler for method: {method}")
    
    def add_middleware(self, middleware: Callable):
        """
        Add middleware to the JSON-RPC processor.
        
        Args:
            middleware: Async middleware function
        """
        self.processor.add_middleware(middleware)
    
    def method_handler(self, method: str):
        """
        Decorator for registering method handlers.
        
        Args:
            method: ACP method name
            
        Example:
            @server.method_handler("tasks.create")
            async def handle_task_create(params, context):
                return {"taskId": "123", "status": "SUBMITTED"}
        """
        def decorator(func: Callable):
            self.register_handler(method, func)
            return func
        return decorator
    
    def task_handler(self, method: str):
        """Decorator for task-related method handlers"""
        return self.method_handler(method)
    
    def stream_handler(self, method: str):
        """Decorator for stream-related method handlers"""
        return self.method_handler(method)
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app
    
    def run(
        self, 
        host: str = "0.0.0.0", 
        port: int = 8000, 
        reload: bool = False,
        **kwargs
    ):
        """
        Run the ACP server using uvicorn.
        
        Args:
            host: Host to bind to
            port: Port to bind to  
            reload: Enable auto-reload for development
            **kwargs: Additional uvicorn configuration
        """
        try:
            import uvicorn
            
            logger.info(f"Starting ACP server for {self.agent_name} on {host}:{port}")
            
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                reload=reload,
                **kwargs
            )
        except ImportError:
            raise ImportError(
                "uvicorn is required to run the server. "
                "Install it with: pip install uvicorn[standard]"
            )
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise


# Convenience function for creating a simple server
def create_server(agent_name: str, **kwargs) -> ACPServer:
    """
    Create a new ACP server instance.
    
    Args:
        agent_name: Name of the agent
        **kwargs: Additional configuration options
        
    Returns:
        Configured ACPServer instance
    """
    return ACPServer(agent_name, **kwargs)
