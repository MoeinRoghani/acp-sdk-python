"""
ACP Client Implementation

Main client class for making calls to other ACP agents.
"""

import uuid
from typing import Optional, Dict, Any, Union
import httpx
from pydantic import BaseModel

from ..models.generated import (
    TasksCreateParams, TasksSendParams, TasksGetParams,
    StreamStartParams, StreamMessageParams,
    JsonRpcRequest, JsonRpcResponse, RpcError, Jsonrpc, Method
)
from ..core.json_rpc import JsonRpcError, JsonRpcProcessor
from .auth import OAuth2Handler


class ACPClient:
    """
    Client for making calls to other ACP agents.
    
    Example:
        client = ACPClient(
            base_url="https://apigw-app.com/confluence-agent/v1",
            oauth_token="your-token"
        )
        
        response = await client.tasks_create(
            TasksCreateParams(
                message=Message(content=[Part(type="text", text="Hello")])
            )
        )
    """
    
    def __init__(
        self,
        base_url: str,
        oauth_token: Optional[str] = None,
        oauth_config: Optional[Dict] = None,
        timeout: float = 30.0,
        allow_http: bool = False
    ):
        """
        Initialize ACP client.
        
        Args:
            base_url: Base URL of the target agent (must be HTTPS unless allow_http=True)
            oauth_token: OAuth2 bearer token (required for ACP compliance)
            oauth_config: OAuth2 configuration for automatic token refresh
            timeout: Request timeout in seconds
            allow_http: Allow HTTP for local testing (INSECURE - only for development)
            
        Raises:
            ValueError: If base_url is not HTTPS or OAuth2 token is missing
        """
        # Validate HTTPS requirement (ACP protocol mandatory)
        if not allow_http and not base_url.startswith('https://'):
            raise ValueError(
                "ACP protocol requires HTTPS only. "
                f"Invalid URL: {base_url}. Use https:// instead, or set allow_http=True for local testing."
            )
        
        # Validate OAuth2 requirement (ACP protocol mandatory) 
        if not oauth_token and not oauth_config:
            raise ValueError(
                "ACP protocol requires OAuth2 authentication. "
                "Provide either 'oauth_token' or 'oauth_config'."
            )
            
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Setup authentication
        self.auth = OAuth2Handler(oauth_token, oauth_config)
        
        # Setup HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": "ACP-SDK-Python/1.0.0"}
        )
    
    async def tasks_create(self, params: TasksCreateParams) -> Dict[str, Any]:
        """
        Create a new task for another agent.
        
        Args:
            params: Task creation parameters
            
        Returns:
            Task creation response with taskId and status
            
        Raises:
            JsonRpcError: If the agent returns an error
            NetworkError: If there's a network issue
            TimeoutError: If the request times out
        """
        request = JsonRpcRequest(
            jsonrpc=Jsonrpc.field_2_0,
            method=Method.tasks_create,
            params=params.model_dump(by_alias=True, mode='json'),
            id=self._generate_id()
        )
        
        response_data = await self._call(request)
        return response_data["result"]
    
    async def tasks_send(self, params: TasksSendParams) -> Dict[str, Any]:
        """Send message to existing task."""
        request = JsonRpcRequest(
            jsonrpc=Jsonrpc.field_2_0,
            method=Method.tasks_send,
            params=params.model_dump(by_alias=True, mode='json'),
            id=self._generate_id()
        )
        
        response_data = await self._call(request)
        return response_data["result"]
    
    async def tasks_get(self, params: TasksGetParams) -> Dict[str, Any]:
        """Get task status and result."""
        request = JsonRpcRequest(
            jsonrpc=Jsonrpc.field_2_0,
            method=Method.tasks_get,
            params=params.model_dump(by_alias=True, mode='json'),
            id=self._generate_id()
        )
        
        response_data = await self._call(request)
        return response_data["result"]
    
    async def stream_start(self, params: StreamStartParams) -> Dict[str, Any]:
        """Start real-time stream with agent."""
        request = JsonRpcRequest(
            jsonrpc=Jsonrpc.field_2_0,
            method=Method.stream_start,
            params=params.model_dump(by_alias=True, mode='json'),
            id=self._generate_id()
        )
        
        response_data = await self._call(request)
        return response_data["result"]
    
    async def stream_message(self, params: StreamMessageParams) -> Dict[str, Any]:
        """Send message in active stream."""
        request = JsonRpcRequest(
            jsonrpc=Jsonrpc.field_2_0,
            method=Method.stream_message,
            params=params.model_dump(by_alias=True, mode='json'),
            id=self._generate_id()
        )
        
        response_data = await self._call(request)
        return response_data["result"]
    
    async def _call(self, request: JsonRpcRequest) -> Dict[str, Any]:
        """
        Make JSON-RPC call to agent.
        
        Args:
            request: JSON-RPC request object
            
        Returns:
            JSON-RPC response data
            
        Raises:
            JsonRpcError: If the agent returns an error
            NetworkError: If there's a network issue
            TimeoutError: If the request times out
            AuthenticationError: If authentication fails
        """
        try:
            # Get authentication headers
            auth_headers = await self.auth.get_headers()
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                **auth_headers
            }
            
            # Make request
            response = await self.client.post(
                f"{self.base_url}/jsonrpc",
                json=request.model_dump(by_alias=True, mode='json'),
                headers=headers
            )
            
            # Handle HTTP errors
            if response.status_code == 401:
                raise JsonRpcError(
                    JsonRpcProcessor.AUTHENTICATION_FAILED,
                    "Authentication failed"
                )
            elif response.status_code == 403:
                raise JsonRpcError(
                    JsonRpcProcessor.PERMISSION_DENIED,
                    "Insufficient permissions"
                )
            
            response.raise_for_status()
            
            # Parse JSON-RPC response
            data = response.json()
            
            # Handle JSON-RPC errors
            if "error" in data and data["error"] is not None:
                error = RpcError.model_validate(data["error"])
                raise JsonRpcError(
                    code=error.code,
                    message=error.message,
                    data=error.data
                )
            
            return data
            
        except httpx.TimeoutException:
            raise JsonRpcError(
                JsonRpcProcessor.INTERNAL_ERROR,
                f"Request to {self.base_url} timed out"
            )
        except httpx.NetworkError as e:
            raise JsonRpcError(
                JsonRpcProcessor.INTERNAL_ERROR,
                f"Network error: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise JsonRpcError(
                JsonRpcProcessor.INTERNAL_ERROR,
                f"HTTP error {e.response.status_code}: {e.response.text}"
            )
    
    def _generate_id(self) -> str:
        """Generate unique request ID."""
        return str(uuid.uuid4())
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close() 