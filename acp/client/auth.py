"""OAuth2 authentication handler for ACP client."""

from typing import Optional, List
from pydantic import BaseModel


class OAuth2Config(BaseModel):
    """
    OAuth2 configuration for ACP client authentication.
    
    Based on the ACP specification requirements for OAuth2 authentication.
    """
    token_url: str
    client_id: str
    client_secret: str
    scopes: List[str]
    cache_tokens: bool = True
    refresh_threshold: int = 300  # seconds before expiry to refresh


class OAuth2Handler:
    """Handle OAuth2 authentication for ACP requests"""
    
    def __init__(self, token: Optional[str] = None, config: Optional[OAuth2Config] = None):
        self.token = token
        self.config = config
    
    async def get_headers(self):
        """Get authentication headers"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
