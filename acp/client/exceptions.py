"""Client-specific exceptions."""

class ClientError(Exception):
    """Base client error"""
    pass

class NetworkError(ClientError):
    """Network-related error"""
    pass

class TimeoutError(ClientError):
    """Request timeout error"""
    pass
