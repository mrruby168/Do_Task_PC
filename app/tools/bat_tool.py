"""
PC Tool Server - BAT Tool

Tool implementation for executing batch files safely.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.tools.base import BaseTool, ToolManifest


logger = logging.getLogger(__name__)


class BatTool(BaseTool):
    """
    Tool for executing batch files within sandbox.
    
    BAT files must be:
    - Located in Tool Root
    - Registered in manifest
    - Enabled by user
    - Have valid arguments
    """
    
    def __init__(self, manifest: ToolManifest, tool_dir: Path):
        """
        Initialize BAT tool.
        
        Args:
            manifest: Tool manifest
            tool_dir: Tool directory path
        """
        super().__init__(manifest)
        self.tool_dir = tool_dir
        self.entry_path = tool_dir / manifest.entry if manifest.entry else None
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the batch file.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Execution result
        """
        try:
            if not self.entry_path or not self.entry_path.exists():
                return {
                    "success": False,
                    "error": f"Batch file not found: {self.entry_path}",
                }
            
            # Build command with validated arguments
            cmd_args = self._build_command(arguments)
            
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.tool_dir),
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=60.0  # 60 second timeout
                )
                
                return {
                    "success": process.returncode == 0,
                    "returncode": process.returncode,
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                }
                
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "error": "Execution timeout (60s)",
                }
                
        except Exception as e:
            logger.exception(f"BAT tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _build_command(self, arguments: Dict[str, Any]) -> List[str]:
        """
        Build command line from arguments.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Command list
        """
        cmd = [str(self.entry_path)]
        
        # Add arguments as parameters
        # This is safe because arguments are already validated
        for key, value in arguments.items():
            cmd.append(f"/{key}:{value}")
        
        return cmd
    
    async def validate(self, arguments: Dict[str, Any]) -> bool:
        """
        Validate arguments for BAT execution.
        
        Args:
            arguments: Arguments to validate
            
        Returns:
            True if valid
        """
        # Check that entry point exists
        if not self.entry_path or not self.entry_path.exists():
            return False
        
        # Validate against schema if defined
        if self.manifest.arguments_schema:
            from app.security.validator import get_argument_validator
            validator = get_argument_validator()
            
            try:
                validator.validate(arguments, self.manifest.arguments_schema)
                return True
            except Exception:
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
            "entry_point": str(self.entry_path) if self.entry_path else None,
            "arguments_schema": self.manifest.arguments_schema,
        }
