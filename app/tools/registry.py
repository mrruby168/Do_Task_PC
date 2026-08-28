"""
PC Tool Server - Tool Registry

Central registry for all available tools.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.tools.base import BaseTool, ToolManifest, ToolType


logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for managing tools.
    
    Tools are registered with their manifest and can be
    looked up by name.
    """
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._manifests: Dict[str, Dict[str, Any]] = {}
    
    def register(self, tool: BaseTool) -> bool:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
            
        Returns:
            True if successful, False otherwise
        """
        try:
            name = tool.name
            
            if name in self._tools:
                logger.warning(f"Tool '{name}' already registered, updating")
            
            self._tools[name] = tool
            self._manifests[name] = tool.get_manifest()
            
            logger.info(f"Tool '{name}' registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool: {e}")
            return False
    
    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            tool_name: Name of tool to unregister
            
        Returns:
            True if successful, False otherwise
        """
        if tool_name not in self._tools:
            return False
        
        del self._tools[tool_name]
        del self._manifests[tool_name]
        
        logger.info(f"Tool '{tool_name}' unregistered")
        return True
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get tool manifest by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool manifest dict or None
        """
        return self._manifests.get(tool_name)
    
    def get_tool_instance(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get tool instance by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance or None
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.
        
        Returns:
            List of tool manifests
        """
        return list(self._manifests.values())
    
    def list_enabled_tools(self) -> List[Dict[str, Any]]:
        """
        List all enabled tools.
        
        Returns:
            List of enabled tool manifests
        """
        return [
            manifest for manifest in self._manifests.values()
            if manifest.get("enabled", False)
        ]
    
    def enable_tool(self, tool_name: str) -> bool:
        """
        Enable a tool.
        
        Args:
            tool_name: Name of tool to enable
            
        Returns:
            True if successful, False otherwise
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return False
        
        tool.set_enabled(True)
        self._manifests[tool_name]["enabled"] = True
        
        logger.info(f"Tool '{tool_name}' enabled")
        return True
    
    def disable_tool(self, tool_name: str) -> bool:
        """
        Disable a tool.
        
        Args:
            tool_name: Name of tool to disable
            
        Returns:
            True if successful, False otherwise
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return False
        
        tool.set_enabled(False)
        self._manifests[tool_name]["enabled"] = False
        
        logger.info(f"Tool '{tool_name}' disabled")
        return True
    
    def get_stats(self) -> Dict[str, int]:
        """Get registry statistics."""
        total = len(self._tools)
        enabled = sum(1 for m in self._manifests.values() if m.get("enabled", False))
        
        return {
            "total": total,
            "enabled": enabled,
            "disabled": total - enabled,
        }
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._manifests.clear()
        logger.info("Tool registry cleared")


# Global registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def reset_tool_registry() -> None:
    """Reset the global tool registry (for testing)."""
    global _tool_registry
    if _tool_registry is not None:
        _tool_registry.clear()
    _tool_registry = None
