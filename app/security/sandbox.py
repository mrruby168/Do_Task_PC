"""
PC Tool Server - Sandbox Security

Path validation and sandbox enforcement to prevent path traversal attacks.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

from app.config import get_config


class SandboxError(Exception):
    """Exception raised when sandbox violation is detected."""
    pass


class SandboxManager:
    """Manages sandbox security for file operations."""
    
    def __init__(self):
        """Initialize sandbox manager."""
        self.config = get_config()
    
    def get_tool_root(self) -> Optional[Path]:
        """Get the configured Tool Root path."""
        return self.config.tool_root
    
    def is_sandbox_enabled(self) -> bool:
        """Check if sandbox is enabled."""
        return self.config.SANDBOX_ENABLED
    
    def validate_path(self, path: str) -> Tuple[bool, str]:
        """
        Validate that a path is within the Tool Root sandbox.
        
        Args:
            path: The path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_sandbox_enabled():
            return True, ""
        
        tool_root = self.get_tool_root()
        
        if tool_root is None:
            return False, "Tool Root is not configured"
        
        try:
            # Resolve to absolute path
            path_obj = Path(path)
            
            # Check for path traversal patterns
            path_str = str(path)
            if ".." in path_str:
                return False, "Path traversal detected (..)"
            
            # Normalize and resolve paths
            resolved_path = path_obj.resolve()
            resolved_root = tool_root.resolve()
            
            # Check if path is within tool root
            try:
                resolved_path.relative_to(resolved_root)
            except ValueError:
                return False, f"Path is outside Tool Root: {path}"
            
            # Check for symlink escapes
            if path_obj.is_symlink():
                symlink_target = path_obj.readlink().resolve()
                try:
                    symlink_target.relative_to(resolved_root)
                except ValueError:
                    return False, "Symlink points outside Tool Root"
            
            return True, ""
            
        except Exception as e:
            return False, f"Path validation error: {str(e)}"
    
    def safe_path(self, path: str) -> Path:
        """
        Get a safe Path object within the sandbox.
        
        Args:
            path: Relative or absolute path
            
        Returns:
            Safe Path object
            
        Raises:
            SandboxError: If path is not safe
        """
        is_valid, error_msg = self.validate_path(path)
        
        if not is_valid:
            raise SandboxError(error_msg)
        
        return Path(path).resolve()
    
    def is_system_path(self, path: str) -> bool:
        """Check if path is a blocked system path."""
        return self.config.is_system_path(path)
    
    def validate_tool_root(self, path: str) -> Tuple[bool, str]:
        """
        Validate a new Tool Root path.
        
        Args:
            path: The path to validate as Tool Root
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.config.validate_tool_root(path)
    
    def check_file_access(self, file_path: str, mode: str = "read") -> Tuple[bool, str]:
        """
        Check if file access is allowed.
        
        Args:
            file_path: Path to the file
            mode: Access mode (read, write, execute)
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        is_valid, error_msg = self.validate_path(file_path)
        
        if not is_valid:
            return False, error_msg
        
        # Additional checks based on mode
        path_obj = Path(file_path)
        
        if mode == "write":
            # Check if parent directory exists and is writable
            parent = path_obj.parent
            if not parent.exists():
                return False, f"Parent directory does not exist: {parent}"
        
        return True, ""


# Global sandbox manager instance
sandbox_manager = SandboxManager()


def get_sandbox_manager() -> SandboxManager:
    """Get the global sandbox manager instance."""
    return sandbox_manager
