"""
PC Tool Server - Security Module

Authentication, authorization, and security utilities.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import get_config


# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class SecurityManager:
    """Manages authentication and authorization."""
    
    def __init__(self):
        """Initialize security manager."""
        self.config = get_config()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify API key.
        
        Args:
            api_key: The API key to verify
            
        Returns:
            True if valid, False otherwise
        """
        if not self.config.AUTHENTICATION_ENABLED:
            return True
        
        return secrets.compare_digest(api_key, self.config.API_KEY)
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Optional expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.config.API_KEY, 
            algorithm=ALGORITHM
        )
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[dict]:
        """
        Decode a JWT token.
        
        Args:
            token: The JWT token to decode
            
        Returns:
            Decoded data or None if invalid
        """
        try:
            payload = jwt.decode(
                token, 
                self.config.API_KEY, 
                algorithms=[ALGORITHM]
            )
            return payload
        except JWTError:
            return None


# Global security manager instance
security_manager = SecurityManager()


def get_security_manager() -> SecurityManager:
    """Get the global security manager instance."""
    return security_manager
