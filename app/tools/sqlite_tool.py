"""
PC Tool Server - SQLite Tool

Tool for safe SQLite database operations.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.tools.base import BaseTool, ToolManifest


logger = logging.getLogger(__name__)


class SqliteTool(BaseTool):
    """Tool for SQLite database operations."""
    
    def __init__(self, manifest: ToolManifest, tool_dir: Path):
        """Initialize SQLite tool."""
        super().__init__(manifest)
        self.tool_dir = tool_dir
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQLite operation."""
        try:
            action = arguments.get("action", "query")
            db_path = arguments.get("db_path", "")
            query = arguments.get("query", "")
            
            # Validate path
            from app.security.sandbox import get_sandbox_manager
            sandbox = get_sandbox_manager()
            
            is_valid, error_msg = sandbox.validate_path(db_path)
            if not is_valid:
                return {"success": False, "error": error_msg}
            
            if action == "query":
                params = arguments.get("params", [])
                return await self._execute_query(db_path, query, params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.exception(f"SQLite tool execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_query(
        self, 
        db_path: str, 
        query: str, 
        params: List[Any]
    ) -> Dict[str, Any]:
        """Execute SQL query."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                result = {
                    "columns": columns,
                    "rows": [dict(zip(columns, row)) for row in rows],
                    "count": len(rows),
                }
            else:
                conn.commit()
                result = {
                    "rows_affected": cursor.rowcount,
                }
            
            conn.close()
            
            return {"success": True, **result}
            
        except sqlite3.Error as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    async def validate(self, arguments: Dict[str, Any]) -> bool:
        """Validate arguments."""
        required_fields = ["db_path", "query"]
        
        for field in required_fields:
            if field not in arguments:
                return False
        
        # Basic SQL injection prevention
        query = arguments.get("query", "")
        dangerous_patterns = ["DROP TABLE", "DELETE FROM", "TRUNCATE"]
        
        for pattern in dangerous_patterns:
            if pattern.upper() in query.upper():
                # Only allow if permission is DANGEROUS
                if self.permission != "DANGEROUS":
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
            "actions": ["query"],
        }
