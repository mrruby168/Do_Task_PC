"""
PC Tool Server - Tool Discovery

Automatic discovery of tools from Tool Root directory.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.config import get_config
from app.tools.base import BaseTool, ToolManifest, ToolType
from app.tools.registry import get_tool_registry


logger = logging.getLogger(__name__)


class ToolDiscovery:
    """
    Discovers and loads tools from Tool Root directory.
    
    Scans for manifest.json files and validates tool configuration.
    """
    
    def __init__(self):
        """Initialize tool discovery."""
        self.config = get_config()
        self.registry = get_tool_registry()
    
    def discover(self) -> List[Dict[str, Any]]:
        """
        Discover all tools in Tool Root.
        
        Returns:
            List of discovered tool manifests
        """
        tool_root = self.config.tool_root
        
        if not tool_root:
            logger.warning("Tool Root not configured, skipping discovery")
            return []
        
        if not tool_root.exists():
            logger.warning(f"Tool Root does not exist: {tool_root}")
            return []
        
        discovered_tools = []
        
        # Scan for manifest.json files
        for manifest_path in tool_root.rglob("manifest.json"):
            try:
                tool_info = self._load_manifest(manifest_path)
                if tool_info:
                    discovered_tools.append(tool_info)
            except Exception as e:
                logger.error(f"Failed to load manifest {manifest_path}: {e}")
        
        logger.info(f"Discovered {len(discovered_tools)} tools")
        return discovered_tools
    
    def _load_manifest(self, manifest_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load and validate a tool manifest.
        
        Args:
            manifest_path: Path to manifest.json
            
        Returns:
            Tool manifest dict or None
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # Validate required fields
            if "name" not in manifest_data:
                logger.error(f"Manifest missing 'name' field: {manifest_path}")
                return None
            
            # Create manifest object
            manifest = ToolManifest(**manifest_data)
            
            # Validate entry point exists
            tool_dir = manifest_path.parent
            entry_path = tool_dir / manifest.entry
            
            if manifest.entry and not entry_path.exists():
                logger.warning(
                    f"Tool entry point not found: {entry_path}. "
                    f"Tool '{manifest.name}' may not function correctly."
                )
            
            # Register the tool
            tool_instance = self._create_tool_instance(manifest, tool_dir)
            
            if tool_instance:
                self.registry.register(tool_instance)
                logger.info(f"Registered tool: {manifest.name}")
                return manifest.model_dump()
            
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest {manifest_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading manifest {manifest_path}: {e}")
            return None
    
    def _create_tool_instance(
        self, 
        manifest: ToolManifest, 
        tool_dir: Path
    ) -> Optional[BaseTool]:
        """
        Create a tool instance based on type.
        
        Args:
            manifest: Tool manifest
            tool_dir: Tool directory path
            
        Returns:
            Tool instance or None
        """
        tool_type = manifest.tool_type
        
        try:
            if tool_type == ToolType.BAT:
                from app.tools.bat_tool import BatTool
                return BatTool(manifest, tool_dir)
            elif tool_type == ToolType.JSON:
                from app.tools.json_tool import JsonTool
                return JsonTool(manifest, tool_dir)
            elif tool_type == ToolType.SQLITE:
                from app.tools.sqlite_tool import SqliteTool
                return SqliteTool(manifest, tool_dir)
            elif tool_type == ToolType.BROWSER:
                from app.tools.browser_tool import BrowserTool
                return BrowserTool(manifest, tool_dir)
            else:
                # Custom tool - create generic instance
                from app.tools.custom_tool import CustomTool
                return CustomTool(manifest, tool_dir)
                
        except ImportError as e:
            logger.error(f"Failed to import tool type {tool_type}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create tool instance: {e}")
            return None
    
    def refresh(self) -> int:
        """
        Refresh tool registry by rediscovering all tools.
        
        Returns:
            Number of tools discovered
        """
        # Clear existing registry
        self.registry.clear()
        
        # Rediscover
        discovered = self.discover()
        
        return len(discovered)
    
    def add_tool(self, manifest_data: Dict[str, Any], tool_dir: Path) -> Tuple[bool, str]:
        """
        Add a new tool manually.
        
        Args:
            manifest_data: Tool manifest data
            tool_dir: Tool directory path
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate manifest
            manifest = ToolManifest(**manifest_data)
            
            # Create tool instance
            tool_instance = self._create_tool_instance(manifest, tool_dir)
            
            if not tool_instance:
                return False, "Failed to create tool instance"
            
            # Register
            self.registry.register(tool_instance)
            
            return True, ""
            
        except Exception as e:
            return False, str(e)
    
    def validate_manifest(self, manifest_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a tool manifest.
        
        Args:
            manifest_data: Manifest data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ToolManifest(**manifest_data)
            return True, ""
        except Exception as e:
            return False, str(e)


# Global discovery instance
_tool_discovery: Optional[ToolDiscovery] = None


def get_tool_discovery() -> ToolDiscovery:
    """Get or create the global tool discovery instance."""
    global _tool_discovery
    if _tool_discovery is None:
        _tool_discovery = ToolDiscovery()
    return _tool_discovery
