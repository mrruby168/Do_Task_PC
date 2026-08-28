"""
PC Tool Server - Configuration Module

Centralized configuration management using Pydantic Settings.
Loads configuration from .env file and environment variables.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Optional, List

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Config(BaseSettings):
    """Application configuration with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "PC Tool Server"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8080
    
    # Security
    API_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    AUTHENTICATION_ENABLED: bool = True
    PHONE_APPROVAL_ENABLED: bool = True
    SANDBOX_ENABLED: bool = True
    SYSTEM_DRIVE_BLOCKED: bool = True
    
    # Tool Root
    TOOL_ROOT_PATH: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./pc_tool_server.db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Blocked system paths (Windows)
    BLOCKED_PATHS: List[str] = [
        r"C:\Windows",
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\ProgramData",
        r"C:\Users",
    ]
    
    # System drives to block
    BLOCKED_DRIVES: List[str] = ["C:\\"]
    
    @field_validator("PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @field_validator("API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not default value."""
        if v == "change_this_to_secure_random_string":
            # Generate a new secure key if default
            return secrets.token_urlsafe(32)
        return v
    
    @property
    def tool_root(self) -> Optional[Path]:
        """Get Tool Root as Path object."""
        if self.TOOL_ROOT_PATH:
            return Path(self.TOOL_ROOT_PATH)
        return None
    
    @property
    def log_path(self) -> Path:
        """Get log file path."""
        return Path(self.LOG_FILE)
    
    @property
    def db_path(self) -> str:
        """Get database path."""
        return self.DATABASE_URL
    
    def is_system_path(self, path: str) -> bool:
        """Check if path is a blocked system path."""
        path_normalized = os.path.normpath(path).lower()
        
        # Check blocked drives
        for drive in self.BLOCKED_DRIVES:
            if path_normalized.startswith(drive.lower()):
                return True
        
        # Check blocked paths
        for blocked in self.BLOCKED_PATHS:
            if path_normalized.startswith(blocked.lower()):
                return True
        
        return False
    
    def validate_tool_root(self, path: str) -> tuple[bool, str]:
        """
        Validate Tool Root path.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path:
            return False, "Tool Root path is empty"
        
        path_obj = Path(path)
        
        if not path_obj.exists():
            return False, f"Path does not exist: {path}"
        
        if not path_obj.is_dir():
            return False, f"Path is not a directory: {path}"
        
        if self.is_system_path(path):
            return False, f"Cannot use system path: {path}"
        
        # Check if it's a system drive root
        path_str = str(path_obj.resolve())
        if path_str.endswith(":\\") or path_str.endswith(":/"):
            return False, f"Cannot use system drive root: {path}"
        
        return True, ""


# Global config instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config
