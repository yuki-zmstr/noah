"""
Authentication service for Noah Reading Agent using Amazon Cognito.
Handles JWT token validation, user authentication, and authorization.
"""

import os
import jwt
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class CognitoUser(BaseModel):
    """Cognito user information extracted from JWT token."""
    user_id: str
    email: str
    email_verified: bool
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    token_use: str
    exp: int
    iat: int


class AuthService:
    """Service for handling Amazon Cognito authentication."""

    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_CLIENT_ID')

        if not self.user_pool_id or not self.client_id:
            logger.warning(
                "Cognito configuration not found. Authentication will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            self.jwks_url = f'https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json'
            self._jwks_cache = None
            self._jwks_cache_time = None

    def _get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set from Cognito, with caching."""
        now = datetime.now(timezone.utc)

        # Cache JWKS for 1 hour
        if (self._jwks_cache is None or
            self._jwks_cache_time is None or
                (now - self._jwks_cache_time).total_seconds() > 3600):

            try:
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_cache_time = now
                logger.info("JWKS cache updated")
            except requests.RequestException as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                if self._jwks_cache is None:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Authentication service unavailable"
                    )

        return self._jwks_cache

    def _get_public_key(self, token_header: Dict[str, Any]) -> str:
        """Get the public key for JWT verification."""
        kid = token_header.get('kid')
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header"
            )

        jwks = self._get_jwks()

        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                # Convert JWK to PEM format
                return jwt.algorithms.RSAAlgorithm.from_jwk(key)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Public key not found"
        )

    def verify_token(self, token: str) -> CognitoUser:
        """
        Verify JWT token from Amazon Cognito and extract user information.

        Args:
            token: JWT token from Cognito

        Returns:
            CognitoUser: Verified user information

        Raises:
            HTTPException: If token is invalid or expired
        """
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Authentication is not configured"
            )

        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)

            # Get public key for verification
            public_key = self._get_public_key(unverified_header)

            # Verify and decode token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=f'https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}'
            )

            # Extract user information
            user_info = CognitoUser(
                user_id=payload.get('sub'),
                email=payload.get('email'),
                email_verified=payload.get('email_verified', False),
                given_name=payload.get('given_name'),
                family_name=payload.get('family_name'),
                token_use=payload.get('token_use'),
                exp=payload.get('exp'),
                iat=payload.get('iat')
            )

            logger.info(f"Token verified for user: {user_info.email}")
            return user_info

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )

    def extract_user_id(self, token: str) -> str:
        """
        Extract user ID from JWT token without full verification.
        Use only when you need the user ID quickly and token validity is not critical.

        Args:
            token: JWT token from Cognito

        Returns:
            str: User ID (sub claim)
        """
        try:
            # Decode without verification (for user ID extraction only)
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get('sub')
        except Exception as e:
            logger.warning(f"Failed to extract user ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired without full verification.

        Args:
            token: JWT token from Cognito

        Returns:
            bool: True if token is expired
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = payload.get('exp')
            if exp:
                return datetime.now(timezone.utc).timestamp() > exp
            return True
        except Exception:
            return True


# Global auth service instance
auth_service = AuthService()


def get_current_user(authorization: str) -> CognitoUser:
    """
    FastAPI dependency to get current authenticated user.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        CognitoUser: Current authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(' ')[1]
    return auth_service.verify_token(token)


def get_user_id_from_token(authorization: str) -> str:
    """
    FastAPI dependency to extract user ID from token.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        str: User ID
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(' ')[1]
    return auth_service.extract_user_id(token)
