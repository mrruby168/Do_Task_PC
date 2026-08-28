"""
PC Tool Server - Approval Manager

Manages phone approval workflow for dangerous operations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.security.permissions import ApprovalStatus


logger = logging.getLogger(__name__)


class Approval:
    """Represents a single approval request."""
    
    def __init__(
        self,
        request_id: str,
        task_id: str,
        tool: str,
        action: str,
        arguments: Dict[str, Any],
        permission: str,
        risk_level: int,
    ):
        """Initialize approval."""
        self.approval_id = f"approval_{uuid.uuid4().hex[:8]}"
        self.request_id = request_id
        self.task_id = task_id
        self.tool = tool
        self.action = action
        self.arguments = arguments
        self.permission = permission
        self.risk_level = risk_level
        self.status = ApprovalStatus.WAITING
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(minutes=5)  # 5 min expiry
        self.decided_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert approval to dictionary."""
        return {
            "approval_id": self.approval_id,
            "request_id": self.request_id,
            "task_id": self.task_id,
            "tool": self.tool,
            "action": self.action,
            "arguments": self.arguments,
            "permission": self.permission,
            "risk_level": self.risk_level,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }
    
    def is_expired(self) -> bool:
        """Check if approval has expired."""
        return datetime.utcnow() > self.expires_at
    
    def approve(self) -> bool:
        """Approve the request."""
        if self.status.is_final():
            return False
        
        if self.is_expired():
            self.status = ApprovalStatus.EXPIRED
            return False
        
        self.status = ApprovalStatus.APPROVED
        self.decided_at = datetime.utcnow()
        return True
    
    def reject(self) -> bool:
        """Reject the request."""
        if self.status.is_final():
            return False
        
        self.status = ApprovalStatus.REJECTED
        self.decided_at = datetime.utcnow()
        return True


class ApprovalManager:
    """Manages all approval requests."""
    
    def __init__(self):
        """Initialize approval manager."""
        self._approvals: Dict[str, Approval] = {}
        self._max_approvals = 500  # Keep last 500 approvals
    
    def create_approval(
        self,
        request_id: str,
        task_id: str,
        tool: str,
        action: str,
        arguments: Dict[str, Any],
        permission: str,
        risk_level: int = 1,
    ) -> Approval:
        """Create a new approval request."""
        approval = Approval(
            request_id=request_id,
            task_id=task_id,
            tool=tool,
            action=action,
            arguments=arguments,
            permission=permission,
            risk_level=risk_level,
        )
        
        self._approvals[approval.approval_id] = approval
        
        # Cleanup old approvals
        self._cleanup()
        
        logger.info(f"Approval created: {approval.approval_id} for task {task_id}")
        return approval
    
    def get_approval(self, approval_id: str) -> Optional[Approval]:
        """Get approval by ID."""
        return self._approvals.get(approval_id)
    
    def get_approval_by_task(self, task_id: str) -> Optional[Approval]:
        """Get approval by task ID."""
        for approval in self._approvals.values():
            if approval.task_id == task_id:
                return approval
        return None
    
    def list_approvals(
        self,
        status_filter: Optional[ApprovalStatus] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List approvals with optional status filter."""
        approvals = list(self._approvals.values())
        
        # Sort by created_at descending
        approvals.sort(key=lambda a: a.created_at, reverse=True)
        
        # Filter by status
        if status_filter:
            approvals = [a for a in approvals if a.status == status_filter]
        
        # Limit results
        approvals = approvals[:limit]
        
        return [a.to_dict() for a in approvals]
    
    def approve(self, approval_id: str) -> bool:
        """Approve a request."""
        approval = self.get_approval(approval_id)
        
        if not approval:
            return False
        
        if approval.approve():
            logger.info(f"Approval approved: {approval_id}")
            return True
        
        return False
    
    def reject(self, approval_id: str, reason: str = "") -> bool:
        """Reject a request."""
        approval = self.get_approval(approval_id)
        
        if not approval:
            return False
        
        if approval.reject():
            logger.info(f"Approval rejected: {approval_id}")
            return True
        
        return False
    
    def check_approval_status(self, task_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if a task has valid approval.
        
        Returns:
            Tuple of (is_approved, error_message)
        """
        approval = self.get_approval_by_task(task_id)
        
        if not approval:
            return False, "No approval found"
        
        if approval.is_expired():
            if not approval.status.is_final():
                approval.status = ApprovalStatus.EXPIRED
            return False, "Approval expired"
        
        if approval.status == ApprovalStatus.APPROVED:
            return True, None
        
        if approval.status == ApprovalStatus.REJECTED:
            return False, "Approval was rejected"
        
        return False, "Approval pending"
    
    def _cleanup(self) -> None:
        """Remove old expired approvals."""
        if len(self._approvals) > self._max_approvals:
            # Get final status approvals sorted by decided time
            final_approvals = [
                a for a in self._approvals.values()
                if a.status.is_final()
            ]
            final_approvals.sort(key=lambda a: a.decided_at or a.created_at)
            
            # Remove oldest approvals
            to_remove = len(self._approvals) - self._max_approvals + 50
            for approval in final_approvals[:to_remove]:
                del self._approvals[approval.approval_id]
    
    def get_stats(self) -> Dict[str, int]:
        """Get approval statistics."""
        stats = {status.value: 0 for status in ApprovalStatus}
        
        for approval in self._approvals.values():
            stats[approval.status.value] += 1
        
        return stats


# Global approval manager instance
_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """Get or create the global approval manager."""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager
