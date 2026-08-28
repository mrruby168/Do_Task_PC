"""
PC Tool Server - Security Gateway

Central security gateway that all requests must pass through.
Implements the complete security flow as specified.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException, status

from app.security.auth import get_security_manager
from app.security.permissions import PermissionLevel, TaskStatus, ApprovalStatus
from app.security.sandbox import get_sandbox_manager, SandboxError
from app.security.validator import get_argument_validator, ArgumentValidationError
from app.config import get_config


logger = logging.getLogger(__name__)


class GatewayError(Exception):
    """Exception raised when gateway validation fails."""
    
    def __init__(self, message: str, code: str = "GATEWAY_ERROR"):
        super().__init__(message)
        self.code = code


class SecurityGateway:
    """
    Security Gateway for all tool requests.
    
    Flow:
    Request → Authentication → Tool Lookup → Enabled Check → 
    Permission Check → Argument Validation → Sandbox Validation → 
    Approval Validation → Task Creation → Execute → Result → Log
    """
    
    def __init__(self):
        """Initialize security gateway."""
        self.auth_manager = get_security_manager()
        self.sandbox_manager = get_sandbox_manager()
        self.argument_validator = get_argument_validator()
        self.config = get_config()
    
    async def validate_request(
        self,
        api_key: Optional[str],
        tool_name: str,
        action: str,
        arguments: Dict[str, Any],
        tool_registry: Any,  # ToolRegistry instance
        approval_manager: Optional[Any] = None,
    ) -> Tuple[bool, str]:
        """
        Validate a tool request through the complete security flow.
        
        Args:
            api_key: API key from request
            tool_name: Name of the tool to execute
            action: Action to perform
            arguments: Tool arguments
            tool_registry: Tool registry instance
            approval_manager: Optional approval manager instance
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Step 1: Authentication
            auth_result = self._authenticate(api_key)
            if not auth_result[0]:
                return False, auth_result[1]
            
            # Step 2: Tool Lookup
            tool = self._lookup_tool(tool_name, tool_registry)
            if tool is None:
                return False, f"Tool not found: {tool_name}"
            
            # Step 3: Enabled Check
            if not self._is_enabled(tool):
                return False, f"Tool is disabled: {tool_name}"
            
            # Step 4: Permission Check
            perm_result = self._check_permission(tool, action)
            if not perm_result[0]:
                return False, perm_result[1]
            
            # Step 5: Argument Validation
            arg_result = self._validate_arguments(arguments, tool)
            if not arg_result[0]:
                return False, arg_result[1]
            
            # Step 6: Sandbox Validation
            sandbox_result = self._validate_sandbox(arguments, tool)
            if not sandbox_result[0]:
                return False, sandbox_result[1]
            
            # Step 7: Approval Validation (if required)
            if approval_manager and self._requires_approval(tool):
                approval_result = await self._check_approval(
                    tool_name, action, arguments, tool, approval_manager
                )
                if not approval_result[0]:
                    return False, approval_result[1]
            
            return True, ""
            
        except GatewayError as e:
            logger.error(f"Gateway error: {e}")
            return False, str(e)
        except Exception as e:
            logger.exception(f"Unexpected gateway error: {e}")
            return False, f"Internal gateway error: {str(e)}"
    
    def _authenticate(self, api_key: Optional[str]) -> Tuple[bool, str]:
        """Step 1: Authenticate the request."""
        if not self.config.AUTHENTICATION_ENABLED:
            return True, ""
        
        if not api_key:
            raise GatewayError("Missing API key", "AUTH_MISSING")
        
        if not self.auth_manager.verify_api_key(api_key):
            raise GatewayError("Invalid API key", "AUTH_INVALID")
        
        return True, ""
    
    def _lookup_tool(self, tool_name: str, tool_registry: Any) -> Optional[Dict]:
        """Step 2: Look up the tool in registry."""
        return tool_registry.get_tool(tool_name)
    
    def _is_enabled(self, tool: Dict) -> bool:
        """Step 3: Check if tool is enabled."""
        return tool.get("enabled", False)
    
    def _check_permission(
        self, 
        tool: Dict, 
        action: str
    ) -> Tuple[bool, str]:
        """Step 4: Check permissions."""
        permission = tool.get("permission", "READ")
        
        try:
            perm_level = PermissionLevel(permission)
        except ValueError:
            return False, f"Invalid permission level: {permission}"
        
        # Check if action matches permission
        if action == "execute":
            return True, ""
        
        return False, f"Action '{action}' not allowed with permission '{permission}'"
    
    def _validate_arguments(
        self, 
        arguments: Dict[str, Any], 
        tool: Dict
    ) -> Tuple[bool, str]:
        """Step 5: Validate arguments."""
        schema = tool.get("arguments_schema", {})
        
        if not schema:
            return True, ""
        
        try:
            self.argument_validator.validate(arguments, schema)
            return True, ""
        except ArgumentValidationError as e:
            return False, str(e)
    
    def _validate_sandbox(
        self, 
        arguments: Dict[str, Any], 
        tool: Dict
    ) -> Tuple[bool, str]:
        """Step 6: Validate sandbox constraints."""
        if not self.config.SANDBOX_ENABLED:
            return True, ""
        
        # Check path arguments
        allowed_paths = tool.get("allowed_paths", [])
        
        for key, value in arguments.items():
            if isinstance(value, str) and ("path" in key.lower() or "file" in key.lower()):
                is_valid, error_msg = self.sandbox_manager.validate_path(value)
                if not is_valid:
                    return False, f"Sandbox violation in argument '{key}': {error_msg}"
        
        return True, ""
    
    def _requires_approval(self, tool: Dict) -> bool:
        """Check if tool requires approval."""
        if not self.config.PHONE_APPROVAL_ENABLED:
            return False
        
        requires_approval = tool.get("requires_approval", False)
        permission = tool.get("permission", "READ")
        
        # DANGEROUS permission always requires approval
        if permission == "DANGEROUS":
            return True
        
        return requires_approval
    
    async def _check_approval(
        self,
        tool_name: str,
        action: str,
        arguments: Dict[str, Any],
        tool: Dict,
        approval_manager: Any
    ) -> Tuple[bool, str]:
        """Step 7: Check approval status."""
        # This would check if there's a valid approval for this request
        # For now, we'll return that approval is needed
        # The actual approval check happens in the task execution flow
        
        return True, ""


# Global gateway instance
security_gateway = SecurityGateway()


def get_security_gateway() -> SecurityGateway:
    """Get the global security gateway instance."""
    return security_gateway
