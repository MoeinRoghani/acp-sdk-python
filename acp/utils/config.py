"""Configuration management for ACP SDK."""

class ACPConfig:
    """Configuration settings for ACP SDK"""
    
    def __init__(self):
        self.base_url = None
        self.oauth_token = None
        self.timeout = 30.0
