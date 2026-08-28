"""
PC Tool Server - Base Tool

Abstract base class for all tools.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class ToolType(str, Enum):
    """Supported tool types."""
    
    JSON = "JSON"
    SQLITE = "SQLite"
    BROWSER = "Browser"
    BAT = "BAT"
    CUSTOM = "Custom"


class ToolManifest(BaseModel):
    """Tool manifest schema."""
    
    name: str = Field(..., description="Unique tool name")
    version: str = Field(default="1.0.0", description="Tool version")
    description: str = Field(default="", description="Tool description")
    tool_type: str = Field(default="CUSTOM", description="Tool type")
    entry: str = Field(default="", description="Entry point file")
    permission: str = Field(default="READ", description="Permission level")
    enabled: bool = Field(default=False, description="Is tool enabled")
    requires_approval: bool = Field(
        default=False, 
        description="Requires phone approval"
    )
    arguments_schema: Dict[str, Any] = Field(
        default={}, 
        description="Pydantic-compatible schema"
    )
    allowed_paths: List[str] = Field(
        default=[], 
        description="Allowed paths for sandbox"
    )
    metadata: Dict[str, Any] = Field(
        default={}, 
        description="Additional metadata"
    )
    
    class Config:
        extra = "allow"


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    All tools must inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, manifest: ToolManifest):
        """
        Initialize the tool.
        
        Args:
            manifest: Tool manifest with configuration
        """
        self.manifest = manifest
        self.name = manifest.name
        self.version = manifest.version
        self.description = manifest.description
        self.tool_type = ToolType(manifest.tool_type)
        self.permission = manifest.permission
        self.enabled = manifest.enabled
        self.requires_approval = manifest.requires_approval
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given arguments.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Execution result dictionary
            
        Raises:
            Exception: If execution fails
        """
        pass
    
    @abstractmethod
    async def validate(self, arguments: Dict[str, Any]) -> bool:
        """
        Validate arguments before execution.
        
        Args:
            arguments: Arguments to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def describe(self) -> Dict[str, Any]:
        """
        Get tool description.
        
        Returns:
            Tool description dictionary
        """
        pass
    
    def get_manifest(self) -> Dict[str, Any]:
        """Get the tool manifest as a dictionary."""
        return self.manifest.model_dump()
    
    def is_enabled(self) -> bool:
        """Check if tool is enabled."""
        return self.enabled
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the tool."""
        self.enabled = enabled
        self.manifest.enabled = enabled
    
    def _log_execution(
        self, 
        action: str, 
        arguments: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """Log tool execution."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "tool": self.name,
            "action": action,
            "arguments": arguments,
        }
        
        if result:
            log_data["result"] = result
        
        if error:
            log_data["error"] = error
            logger.error(f"Tool execution failed: {log_data}")
        else:
            logger.info(f"Tool executed: {log_data}")
