"""
PC Tool Server - Permission Levels

Defines permission levels for tools and operations.
"""

from __future__ import annotations

from enum import Enum


class PermissionLevel(str, Enum):
    """Permission levels for tools."""
    
    READ = "READ"
    WRITE = "WRITE"
    DANGEROUS = "DANGEROUS"
    
    def requires_approval(self) -> bool:
        """Check if this permission level requires approval."""
        return self == PermissionLevel.DANGEROUS
    
    def get_risk_level(self) -> int:
        """Get risk level (1-3)."""
        risk_map = {
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.DANGEROUS: 3,
        }
        return risk_map[self]


class TaskStatus(str, Enum):
    """Task status values."""
    
    QUEUED = "QUEUED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    
    def is_terminal(self) -> bool:
        """Check if this is a terminal status."""
        return self in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.REJECTED,
            TaskStatus.CANCELLED,
        ]


class ApprovalStatus(str, Enum):
    """Approval status values."""
    
    WAITING = "WAITING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    
    def is_final(self) -> bool:
        """Check if this is a final approval status."""
        return self in [
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.EXPIRED,
        ]
