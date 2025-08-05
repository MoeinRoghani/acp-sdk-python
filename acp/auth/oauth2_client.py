"""
OAuth2 Client Credentials Flow Implementation

Implements proper OAuth2 client credentials flow for machine-to-machine authentication.
Supports standard OAuth2 providers like Auth0, Google, Azure AD, etc.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OAuth2Token:
    """OAuth2 access token with metadata"""
    
    def __init__(self, access_token: str, token_type: str = "Bearer", 
                 expires_in: int = 3600, scope: str = "", **kwargs):
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in
        self.scope = scope
        self.issued_at = datetime.utcnow()
        self.expires_at = self.issued_at + timedelta(seconds=expires_in)
        self.extra = kwargs
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 30 second buffer)"""
        return datetime.utcnow() >= (self.expires_at - timedelta(seconds=30))
    
    @property
    def authorization_header(self) -> str:
        """Get Authorization header value"""
        return f"{self.token_type} {self.access_token}"

class OAuth2ClientCredentials:
    """
    OAuth2 Client Credentials Flow Implementation
    
    Handles getting and refreshing OAuth2 tokens using client credentials grant.
    """
    
    def __init__(
        self, 
        token_url: str,
        client_id: str, 
        client_secret: str,
        scope: Optional[str] = None,
        audience: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize OAuth2 client credentials flow.
        
        Args:
            token_url: OAuth2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            scope: Space-separated list of scopes to request
            audience: OAuth2 audience (for some providers like Auth0)
            timeout: Request timeout in seconds
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.audience = audience
        self.timeout = timeout
        self._current_token: Optional[OAuth2Token] = None
        self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))
    
    async def get_token(self, force_refresh: bool = False) -> OAuth2Token:
        """
        Get a valid OAuth2 access token.
        
        Args:
            force_refresh: Force getting a new token even if current one is valid
            
        Returns:
            Valid OAuth2 token
            
        Raises:
            Exception: If token request fails
        """
        # Return current token if still valid
        if not force_refresh and self._current_token and not self._current_token.is_expired:
            return self._current_token
        
        logger.debug(f"Requesting new OAuth2 token from {self.token_url}")
        
        # Prepare token request
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        if self.scope:
            token_data["scope"] = self.scope
            
        if self.audience:
            token_data["audience"] = self.audience
        
        # Make token request
        try:
            response = await self._http_client.post(
                self.token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"OAuth2 token request failed: {response.status_code} - {error_text}")
                raise Exception(f"OAuth2 token request failed: {response.status_code} - {error_text}")
            
            token_response = response.json()
            
            # Validate response
            if "access_token" not in token_response:
                raise Exception(f"Invalid token response: missing access_token")
            
            # Create token object
            self._current_token = OAuth2Token(
                access_token=token_response["access_token"],
                token_type=token_response.get("token_type", "Bearer"),
                expires_in=token_response.get("expires_in", 3600),
                scope=token_response.get("scope", ""),
                **{k: v for k, v in token_response.items() 
                   if k not in ["access_token", "token_type", "expires_in", "scope"]}
            )
            
            logger.info(f"✅ OAuth2 token obtained successfully (expires in {self._current_token.expires_in}s)")
            logger.debug(f"Token scopes: {self._current_token.scope}")
            
            return self._current_token
            
        except httpx.RequestError as e:
            logger.error(f"OAuth2 token request failed: {e}")
            raise Exception(f"OAuth2 token request failed: {e}")
    
    async def get_authorization_header(self, force_refresh: bool = False) -> str:
        """
        Get Authorization header value with valid token.
        
        Args:
            force_refresh: Force getting a new token
            
        Returns:
            Authorization header value (e.g., "Bearer abc123...")
        """
        token = await self.get_token(force_refresh)
        return token.authorization_header
    
    async def close(self):
        """Close HTTP client"""
        await self._http_client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# Common OAuth2 Provider Configurations
OAUTH2_PROVIDERS = {
    "auth0": {
        "token_url_template": "https://{domain}/oauth/token",
        "audience_required": True,
        "scope_separator": " "
    },
    "google": {
        "token_url": "https://oauth2.googleapis.com/token",
        "audience_required": False,
        "scope_separator": " "
    },
    "azure": {
        "token_url_template": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        "audience_required": False,
        "scope_separator": " "
    },
    "okta": {
        "token_url_template": "https://{domain}/oauth2/v1/token",
        "audience_required": True,
        "scope_separator": " "
    }
}

def create_oauth2_client(
    provider: str,
    client_id: str,
    client_secret: str,
    scope: Optional[str] = None,
    **provider_config
) -> OAuth2ClientCredentials:
    """
    Create OAuth2 client for common providers.
    
    Args:
        provider: Provider name (auth0, google, azure, okta)
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        scope: Space-separated scopes
        **provider_config: Provider-specific config (domain, tenant_id, audience, etc.)
        
    Returns:
        Configured OAuth2 client
        
    Example:
        # Auth0
        client = create_oauth2_client(
            "auth0",
            client_id="your-client-id",
            client_secret="your-secret",
            domain="your-domain.auth0.com",
            audience="https://your-api.com",
            scope="read:users write:users"
        )
        
        # Google
        client = create_oauth2_client(
            "google", 
            client_id="your-client-id",
            client_secret="your-secret",
            scope="https://www.googleapis.com/auth/cloud-platform"
        )
    """
    if provider not in OAUTH2_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Supported: {list(OAUTH2_PROVIDERS.keys())}")
    
    config = OAUTH2_PROVIDERS[provider]
    
    # Build token URL
    if "token_url_template" in config:
        token_url = config["token_url_template"].format(**provider_config)
    else:
        token_url = config["token_url"]
    
    # Build client
    client_kwargs = {
        "token_url": token_url,
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope
    }
    
    # Add audience if required and provided
    if config.get("audience_required") and "audience" in provider_config:
        client_kwargs["audience"] = provider_config["audience"]
    
    return OAuth2ClientCredentials(**client_kwargs)

# CLI for testing OAuth2 flow
async def main():
    """CLI for testing OAuth2 client credentials flow"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OAuth2 client credentials flow")
    parser.add_argument("--token-url", required=True, help="OAuth2 token endpoint URL")
    parser.add_argument("--client-id", required=True, help="OAuth2 client ID")  
    parser.add_argument("--client-secret", required=True, help="OAuth2 client secret")
    parser.add_argument("--scope", help="OAuth2 scopes (space-separated)")
    parser.add_argument("--audience", help="OAuth2 audience")
    
    args = parser.parse_args()
    
    try:
        async with OAuth2ClientCredentials(
            token_url=args.token_url,
            client_id=args.client_id,
            client_secret=args.client_secret,
            scope=args.scope,
            audience=args.audience
        ) as oauth_client:
            
            print("🔐 Testing OAuth2 client credentials flow...")
            token = await oauth_client.get_token()
            
            print(f"✅ Token obtained successfully!")
            print(f"Token Type: {token.token_type}")
            print(f"Expires In: {token.expires_in} seconds")
            print(f"Scopes: {token.scope}")
            print(f"Access Token: {token.access_token[:50]}...")
            print(f"Authorization Header: {token.authorization_header[:70]}...")
            
    except Exception as e:
        print(f"❌ OAuth2 test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())