"""
JWT Token Validation for OAuth2 Providers

Validates JWT tokens from OAuth2 providers using JWKS (JSON Web Key Sets).
Supports standard OAuth2 providers like Auth0, Google, Azure AD, etc.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any
import httpx
import jwt
from jwt import PyJWKClient
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JWTValidator:
    """
    JWT token validator using JWKS from OAuth2 providers.
    
    Validates JWT tokens by:
    1. Fetching public keys from JWKS endpoint
    2. Verifying token signature
    3. Checking token expiration
    4. Validating issuer and audience claims
    """
    
    def __init__(
        self,
        jwks_url: str,
        issuer: str,
        audience: Optional[str] = None,
        algorithms: List[str] = None,
        cache_ttl: int = 300  # 5 minutes
    ):
        """
        Initialize JWT validator.
        
        Args:
            jwks_url: JWKS endpoint URL for fetching public keys
            issuer: Expected token issuer
            audience: Expected token audience (optional)
            algorithms: Allowed JWT algorithms (default: ["RS256"])
            cache_ttl: JWKS cache TTL in seconds
        """
        self.jwks_url = jwks_url
        self.issuer = issuer
        self.audience = audience
        self.algorithms = algorithms or ["RS256"]
        self.cache_ttl = cache_ttl
        
        # Initialize JWKS client for fetching public keys
        self.jwks_client = PyJWKClient(
            jwks_url,
            cache_ttl=cache_ttl,
            max_cached_keys=10
        )
        
        logger.info(f"🔑 JWT validator initialized for issuer: {issuer}")
        logger.debug(f"JWKS URL: {jwks_url}")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return claims.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary containing token claims
            
        Raises:
            jwt.InvalidTokenError: If token is invalid
            jwt.ExpiredSignatureError: If token is expired
            Exception: For other validation errors
        """
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and validate token
            decode_options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "require": ["exp", "iat", "iss"]
            }
            
            # Add audience validation if specified
            if self.audience:
                decode_options["verify_aud"] = True
                decode_options["require"].append("aud")
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=self.algorithms,
                issuer=self.issuer,
                audience=self.audience,
                options=decode_options
            )
            
            logger.debug(f"✅ JWT token validated for subject: {payload.get('sub')}")
            logger.debug(f"Token scopes: {payload.get('scope', payload.get('scp', 'none'))}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise
        except jwt.InvalidAudienceError:
            logger.warning(f"JWT token audience mismatch. Expected: {self.audience}")
            raise
        except jwt.InvalidIssuerError:
            logger.warning(f"JWT token issuer mismatch. Expected: {self.issuer}")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT token validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating JWT token: {e}")
            raise

class OAuth2ProviderValidator:
    """
    Validator factory for common OAuth2 providers.
    
    Provides pre-configured validators for popular OAuth2 providers.
    """
    
    PROVIDER_CONFIGS = {
        "auth0": {
            "jwks_url_template": "https://{domain}/.well-known/jwks.json",
            "issuer_template": "https://{domain}/",
            "algorithms": ["RS256"]
        },
        "google": {
            "jwks_url": "https://www.googleapis.com/oauth2/v3/certs",
            "issuer": "https://accounts.google.com",
            "algorithms": ["RS256"]
        },
        "azure": {
            "jwks_url_template": "https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
            "issuer_template": "https://login.microsoftonline.com/{tenant_id}/v2.0",
            "algorithms": ["RS256"]
        },
        "okta": {
            "jwks_url_template": "https://{domain}/oauth2/v1/keys",
            "issuer_template": "https://{domain}/oauth2",
            "algorithms": ["RS256"]
        }
    }
    
    @classmethod
    def create_validator(
        cls,
        provider: str,
        audience: Optional[str] = None,
        **provider_config
    ) -> JWTValidator:
        """
        Create JWT validator for common OAuth2 providers.
        
        Args:
            provider: Provider name (auth0, google, azure, okta)
            audience: Expected token audience
            **provider_config: Provider-specific config (domain, tenant_id, etc.)
            
        Returns:
            Configured JWT validator
            
        Example:
            # Auth0
            validator = OAuth2ProviderValidator.create_validator(
                "auth0",
                domain="your-domain.auth0.com",
                audience="https://your-api.com"
            )
            
            # Google
            validator = OAuth2ProviderValidator.create_validator(
                "google",
                audience="your-client-id.apps.googleusercontent.com"
            )
        """
        if provider not in cls.PROVIDER_CONFIGS:
            raise ValueError(f"Unknown provider: {provider}. Supported: {list(cls.PROVIDER_CONFIGS.keys())}")
        
        config = cls.PROVIDER_CONFIGS[provider]
        
        # Build JWKS URL
        if "jwks_url_template" in config:
            jwks_url = config["jwks_url_template"].format(**provider_config)
        else:
            jwks_url = config["jwks_url"]
        
        # Build issuer
        if "issuer_template" in config:
            issuer = config["issuer_template"].format(**provider_config)
        else:
            issuer = config["issuer"]
        
        return JWTValidator(
            jwks_url=jwks_url,
            issuer=issuer,
            audience=audience,
            algorithms=config["algorithms"]
        )

# Multiple provider validator for supporting different OAuth2 providers
class MultiProviderJWTValidator:
    """
    JWT validator that supports multiple OAuth2 providers.
    
    Tries to validate tokens against multiple configured providers.
    Useful when your API accepts tokens from different OAuth2 providers.
    """
    
    def __init__(self, validators: Dict[str, JWTValidator]):
        """
        Initialize multi-provider validator.
        
        Args:
            validators: Dictionary mapping provider names to validators
        """
        self.validators = validators
        logger.info(f"🔑 Multi-provider JWT validator initialized with providers: {list(validators.keys())}")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate token against all configured providers.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary containing token claims plus provider info
            
        Raises:
            jwt.InvalidTokenError: If token is invalid for all providers
        """
        last_error = None
        
        for provider_name, validator in self.validators.items():
            try:
                logger.debug(f"Trying to validate token with provider: {provider_name}")
                payload = await validator.validate_token(token)
                
                # Add provider info to payload
                payload["_acp_provider"] = provider_name
                
                logger.info(f"✅ Token validated with provider: {provider_name}")
                return payload
                
            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError) as e:
                logger.debug(f"Token validation failed for provider {provider_name}: {e}")
                last_error = e
                continue
        
        # If we get here, all providers failed
        logger.warning("Token validation failed for all configured providers")
        raise last_error or jwt.InvalidTokenError("Token validation failed for all providers")

# Example configurations for testing
def create_development_validator() -> MultiProviderJWTValidator:
    """
    Create a multi-provider validator for development.
    Configure your OAuth2 providers here.
    """
    validators = {}
    
    # Example: Auth0 configuration
    # validators["auth0"] = OAuth2ProviderValidator.create_validator(
    #     "auth0",
    #     domain="your-domain.auth0.com",
    #     audience="https://your-api.com"
    # )
    
    # Example: Google configuration  
    # validators["google"] = OAuth2ProviderValidator.create_validator(
    #     "google",
    #     audience="your-client-id.apps.googleusercontent.com"
    # )
    
    if not validators:
        raise ValueError("No OAuth2 providers configured. Update create_development_validator() with your providers.")
    
    return MultiProviderJWTValidator(validators)

# CLI for testing JWT validation
async def main():
    """CLI for testing JWT validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test JWT validation")
    parser.add_argument("--jwks-url", required=True, help="JWKS endpoint URL")
    parser.add_argument("--issuer", required=True, help="Expected token issuer")
    parser.add_argument("--audience", help="Expected token audience")
    parser.add_argument("--token", required=True, help="JWT token to validate")
    
    args = parser.parse_args()
    
    try:
        validator = JWTValidator(
            jwks_url=args.jwks_url,
            issuer=args.issuer,
            audience=args.audience
        )
        
        print("🔐 Testing JWT validation...")
        payload = await validator.validate_token(args.token)
        
        print(f"✅ Token validated successfully!")
        print(f"Subject: {payload.get('sub')}")
        print(f"Issuer: {payload.get('iss')}")
        print(f"Audience: {payload.get('aud')}")
        print(f"Expires: {datetime.fromtimestamp(payload.get('exp', 0))}")
        print(f"Scopes: {payload.get('scope', payload.get('scp', 'none'))}")
        
    except Exception as e:
        print(f"❌ JWT validation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())