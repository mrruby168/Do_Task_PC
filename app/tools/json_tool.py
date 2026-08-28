"""
PC Tool Server - JSON Tool

Tool for reading and writing JSON files safely.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.tools.base import BaseTool, ToolManifest


logger = logging.getLogger(__name__)


class JsonTool(BaseTool):
    """Tool for JSON file operations."""
    
    def __init__(self, manifest: ToolManifest, tool_dir: Path):
        """Initialize JSON tool."""
        super().__init__(manifest)
        self.tool_dir = tool_dir
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute JSON operation."""
        try:
            action = arguments.get("action", "read")
            file_path = arguments.get("file_path", "")
            
            # Validate path
            from app.security.sandbox import get_sandbox_manager
            sandbox = get_sandbox_manager()
            
            is_valid, error_msg = sandbox.validate_path(file_path)
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            full_path = Path(file_path)
            
            if action == "read":
                return await self._read_json(full_path)
            elif action == "write":
                data = arguments.get("data", {})
                return await self._write_json(full_path, data)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.exception(f"JSON tool execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file."""
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {"success": True, "data": data}
    
    async def _write_json(self, file_path: Path, data: Any) -> Dict[str, Any]:
        """Write JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return {"success": True, "message": "File written successfully"}
    
    async def validate(self, arguments: Dict[str, Any]) -> bool:
        """Validate arguments."""
        if "file_path" not in arguments:
            return False
        
        action = arguments.get("action", "read")
        if action not in ["read", "write"]:
            return False
        
        if action == "write" and "data" not in arguments:
            return False
        
        return True
    
    def describe(self) -> Dict[str, Any]:
        """Get tool description."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "type": self.tool_type.value,
            "permission": self.permission,
            "enabled": self.enabled,
            "requires_approval": self.requires_approval,
            "actions": ["read", "write"],
        }
