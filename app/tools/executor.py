"""
PC Tool Server - Tool Executor

Executes tools with proper security checks and task management.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.tools.base import BaseTool
from app.tools.registry import get_tool_registry
from app.security.sandbox import get_sandbox_manager


logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes tools with security validation.
    
    All tool executions go through this executor which ensures
    proper validation and logging.
    """
    
    def __init__(self):
        """Initialize tool executor."""
        self.registry = get_tool_registry()
        self.sandbox_manager = get_sandbox_manager()
    
    async def execute(
        self,
        tool_name: str,
        action: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of tool to execute
            action: Action to perform
            arguments: Tool arguments
            
        Returns:
            Execution result dictionary
            
        Raises:
            Exception: If execution fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Get tool instance
            tool_instance = self.registry.get_tool_instance(tool_name)
            
            if not tool_instance:
                return {
                    "success": False,
                    "error": f"Tool not found: {tool_name}",
                    "status": "FAILED",
                }
            
            if not tool_instance.is_enabled():
                return {
                    "success": False,
                    "error": f"Tool is disabled: {tool_name}",
                    "status": "REJECTED",
                }
            
            # Validate arguments
            is_valid = await tool_instance.validate(arguments)
            if not is_valid:
                return {
                    "success": False,
                    "error": "Invalid arguments",
                    "status": "REJECTED",
                }
            
            # Execute based on action
            if action == "execute":
                result = await tool_instance.execute(arguments)
                
                return {
                    "success": True,
                    "tool": tool_name,
                    "action": action,
                    "status": "COMPLETED",
                    "result": result,
                    "duration": (datetime.utcnow() - start_time).total_seconds(),
                }
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "status": "FAILED",
                }
                
        except Exception as e:
            logger.exception(f"Tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "FAILED",
                "duration": (datetime.utcnow() - start_time).total_seconds(),
            }
    
    async def test_tool(
        self,
        tool_name: str,
        test_arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Test a tool execution.
        
        Args:
            tool_name: Name of tool to test
            test_arguments: Optional test arguments
            
        Returns:
            Test result dictionary
        """
        tool = self.registry.get_tool(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
            }
        
        # Use default arguments if none provided
        arguments = test_arguments or {}
        
        return await self.execute(tool_name, "execute", arguments)


# Global executor instance
_tool_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """Get or create the global tool executor."""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor
