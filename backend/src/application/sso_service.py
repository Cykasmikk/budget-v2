from typing import Optional, Dict
import httpx
from urllib.parse import urlencode
from src.domain.user import User
from src.infrastructure.models import TenantModel
import secrets

class SSOService:
    """
    Handles SSO logic:
    1. OIDC Discovery (Metadata)
    2. Authorization URL generation
    3. Token Exchange verification
    """
    
    async def get_provider_metadata(self, discovery_url: str) -> Dict:
        """Fetch OIDC metadata from valid .well-known endpoint"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(discovery_url, timeout=5.0)
            resp.raise_for_status()
            return resp.json()

    async def generate_login_url(self, tenant: TenantModel, callback_url: str) -> str:
        """
        Constructs the OIDC Authorization URL for the given tenant config.
        """
        auth_config = tenant.auth_config or {}
        if not auth_config.get("enabled"):
            raise ValueError("SSO not enabled for this tenant")

        # 1. Get Auth Endpoint
        metadata = auth_config.get("metadata", {})
        auth_endpoint = metadata.get("authorization_endpoint")
        
        # Fallback: if metadata missing, maybe fetch it? (For now assume config saved it)
        if not auth_endpoint:
            # Attempt lazy discovery if issuer present
            if auth_config.get("issuer"):
                meta = await self.get_provider_metadata(auth_config["issuer"])
                auth_endpoint = meta.get("authorization_endpoint")
            else:
                raise ValueError("Missing authorization_endpoint in config")

        # 2. Build Query
        params = {
            "client_id": auth_config.get("client_id"),
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "openid email profile",
            "state": secrets.token_urlsafe(16), # Should store this in session/cookie to verify CSRF
            # "nonce": ... (Optional for Code Flow but good for implicit)
        }
        
        return f"{auth_endpoint}?{urlencode(params)}"

    async def exchange_code(self, tenant: TenantModel, code: str, callback_url: str) -> Dict:
        """
        Exchanges Auth Code for ID Token + Access Token
        """
        auth_config = tenant.auth_config or {}
        
        # Get Token Endpoint
        metadata = auth_config.get("metadata", {})
        token_endpoint = metadata.get("token_endpoint")
        
        if not token_endpoint and auth_config.get("issuer"):
             meta = await self.get_provider_metadata(auth_config["issuer"])
             token_endpoint = meta.get("token_endpoint")

        if not token_endpoint:
            raise ValueError("Missing token_endpoint")
            
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": auth_config.get("client_id"),
                "client_secret": auth_config.get("client_secret"),
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": callback_url
            }
            resp = await client.post(token_endpoint, data=data, timeout=5.0)
            resp.raise_for_status()
            return resp.json()
    async def verify_id_token(self, tenant: TenantModel, id_token: str) -> Dict:
        """
        Verifies the ID Token signature against the Provider's JWKS.
        """
        auth_config = tenant.auth_config or {}
        
        # 1. Get JWKS URI
        metadata = auth_config.get("metadata", {})
        jwks_uri = metadata.get("jwks_uri")
        
        if not jwks_uri and auth_config.get("issuer"):
             meta = await self.get_provider_metadata(auth_config["issuer"])
             jwks_uri = meta.get("jwks_uri")
             
        if not jwks_uri:
            raise ValueError("Missing jwks_uri for token verification")

        # 2. Fetch Keys
        async with httpx.AsyncClient() as client:
            resp = await client.get(jwks_uri, timeout=5.0)
            resp.raise_for_status()
            jwks = resp.json()

        # 3. Verify Signature
        from jose import jwt
        
        # Verify audience (client_id)
        audience = auth_config.get("client_id")
        
        try:
            # decode automatically verifies signature if keys are provided
            # it searches jwks for the key id (kid) in the token header
            payload = jwt.decode(
                id_token,
                jwks,
                algorithms=["RS256"],
                audience=audience,
                issuer=auth_config.get("issuer")
            )
            return payload
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")
