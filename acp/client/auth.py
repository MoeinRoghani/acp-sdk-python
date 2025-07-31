"""OAuth2 authentication handler for ACP client."""

class OAuth2Handler:
    """Handle OAuth2 authentication for ACP requests"""
    
    def __init__(self, token=None, config=None):
        self.token = token
        self.config = config
    
    async def get_headers(self):
        """Get authentication headers"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
