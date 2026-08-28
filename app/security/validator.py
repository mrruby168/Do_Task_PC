"""
PC Tool Server - Argument Validator

Pydantic v2 based argument validation for tool execution.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, ValidationError, create_model


class ArgumentValidationError(Exception):
    """Exception raised when argument validation fails."""
    
    def __init__(self, message: str, errors: Optional[list] = None):
        super().__init__(message)
        self.errors = errors or []


class ArgumentValidator:
    """Validates tool arguments using Pydantic schemas."""
    
    def __init__(self):
        """Initialize argument validator."""
        pass
    
    def validate(
        self, 
        arguments: Dict[str, Any], 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate arguments against a schema.
        
        Args:
            arguments: The arguments to validate
            schema: Pydantic-compatible schema definition
            
        Returns:
            Validated arguments
            
        Raises:
            ArgumentValidationError: If validation fails
        """
        try:
            # Create dynamic model from schema
            model = self._create_model_from_schema(schema)
            
            # Validate arguments
            validated = model(**arguments)
            
            # Return as dict
            return validated.model_dump()
            
        except ValidationError as e:
            errors = [
                {
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in e.errors()
            ]
            raise ArgumentValidationError(
                f"Argument validation failed: {e.error_count()} error(s)",
                errors=errors
            )
    
    def _create_model_from_schema(
        self, 
        schema: Dict[str, Any]
    ) -> Type[BaseModel]:
        """
        Create a Pydantic model from a schema definition.
        
        Args:
            schema: Schema definition with field types and constraints
            
        Returns:
            Dynamic Pydantic model class
        """
        fields = {}
        
        for field_name, field_def in schema.get("properties", {}).items():
            field_type = self._parse_type(field_def.get("type", "string"))
            default = field_def.get("default", ...)
            
            # Check if field is required
            required_fields = schema.get("required", [])
            if field_name not in required_fields and default is not ...:
                field_type = Optional[field_type]
            
            fields[field_name] = (field_type, default)
        
        # Add additional properties check
        extra = schema.get("additionalProperties", False)
        if extra is False:
            # Forbid extra fields
            model_config = type(
                "Config", 
                (), 
                {"extra": "forbid"}
            )
        else:
            model_config = type(
                "Config", 
                (), 
                {"extra": "allow"}
            )
        
        model = create_model(
            "DynamicArgumentsModel",
            __config__=model_config,
            **fields
        )
        
        return model
    
    def _parse_type(self, type_str: str) -> Type:
        """
        Parse a JSON Schema type string to Python type.
        
        Args:
            type_str: JSON Schema type string
            
        Returns:
            Corresponding Python type
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        
        return type_map.get(type_str, str)
    
    def validate_path_argument(
        self, 
        path: str, 
        allowed_patterns: Optional[list] = None
    ) -> str:
        """
        Validate a path argument for security.
        
        Args:
            path: The path to validate
            allowed_patterns: Optional list of allowed path patterns
            
        Returns:
            Validated path
            
        Raises:
            ArgumentValidationError: If path is invalid
        """
        # Check for dangerous patterns
        dangerous_patterns = ["..", "\\\\", "//", "|", "&", ";", "`", "$"]
        
        for pattern in dangerous_patterns:
            if pattern in path:
                raise ArgumentValidationError(
                    f"Path contains dangerous pattern: {pattern}"
                )
        
        # Check for shell injection
        shell_chars = ["$", "`", "(", ")", "{", "}", "[", "]", "<", ">"]
        for char in shell_chars:
            if char in path:
                raise ArgumentValidationError(
                    f"Path contains shell special character: {char}"
                )
        
        return path


# Global validator instance
argument_validator = ArgumentValidator()


def get_argument_validator() -> ArgumentValidator:
    """Get the global argument validator instance."""
    return argument_validator
