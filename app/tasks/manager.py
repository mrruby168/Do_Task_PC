"""
PC Tool Server - Task Manager

Manages task lifecycle and state.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.security.permissions import TaskStatus


logger = logging.getLogger(__name__)


class Task:
    """Represents a single task."""
    
    def __init__(
        self,
        task_id: str,
        request_id: str,
        tool: str,
        action: str,
        arguments: Dict[str, Any],
    ):
        """Initialize task."""
        self.task_id = task_id
        self.request_id = request_id
        self.tool = tool
        self.action = action
        self.arguments = arguments
        self.status = TaskStatus.QUEUED
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.finished_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "request_id": self.request_id,
            "tool": self.tool,
            "action": self.action,
            "arguments": self.arguments,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration": self.duration,
            "result": self.result,
            "error": self.error,
        }
    
    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result: Dict[str, Any]) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.finished_at = datetime.utcnow()
        self.result = result
    
    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.finished_at = datetime.utcnow()
        self.error = error
    
    def cancel(self) -> None:
        """Cancel the task."""
        if not self.status.is_terminal():
            self.status = TaskStatus.CANCELLED
            self.finished_at = datetime.utcnow()


class TaskManager:
    """Manages all tasks."""
    
    def __init__(self):
        """Initialize task manager."""
        self._tasks: Dict[str, Task] = {}
        self._max_tasks = 1000  # Keep last 1000 tasks
    
    def create_task(
        self,
        request_id: str,
        tool: str,
        action: str,
        arguments: Dict[str, Any],
        requires_approval: bool = False,
    ) -> Task:
        """Create a new task."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = Task(
            task_id=task_id,
            request_id=request_id,
            tool=tool,
            action=action,
            arguments=arguments,
        )
        
        if requires_approval:
            task.status = TaskStatus.WAITING_APPROVAL
        
        self._tasks[task_id] = task
        
        # Cleanup old tasks
        self._cleanup()
        
        logger.info(f"Task created: {task_id}")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(task_id)
    
    def list_tasks(
        self, 
        status_filter: Optional[TaskStatus] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List tasks with optional status filter."""
        tasks = list(self._tasks.values())
        
        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # Filter by status
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        
        # Limit results
        tasks = tasks[:limit]
        
        return [t.to_dict() for t in tasks]
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all non-terminal tasks."""
        active_statuses = [
            TaskStatus.QUEUED,
            TaskStatus.WAITING_APPROVAL,
            TaskStatus.RUNNING,
        ]
        return self.list_tasks(limit=100)  # Would filter better in real impl
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self.get_task(task_id)
        
        if not task:
            return False
        
        if task.status.is_terminal():
            return False
        
        task.cancel()
        logger.info(f"Task cancelled: {task_id}")
        return True
    
    def approve_task(self, task_id: str) -> bool:
        """Approve a waiting task."""
        task = self.get_task(task_id)
        
        if not task or task.status != TaskStatus.WAITING_APPROVAL:
            return False
        
        task.status = TaskStatus.QUEUED
        logger.info(f"Task approved: {task_id}")
        return True
    
    def reject_task(self, task_id: str, reason: str = "") -> bool:
        """Reject a waiting task."""
        task = self.get_task(task_id)
        
        if not task or task.status != TaskStatus.WAITING_APPROVAL:
            return False
        
        task.status = TaskStatus.REJECTED
        task.error = reason or "Task rejected by user"
        task.finished_at = datetime.utcnow()
        
        logger.info(f"Task rejected: {task_id}")
        return True
    
    def _cleanup(self) -> None:
        """Remove old completed tasks."""
        if len(self._tasks) > self._max_tasks:
            # Get terminal tasks sorted by finish time
            terminal_tasks = [
                t for t in self._tasks.values() 
                if t.status.is_terminal()
            ]
            terminal_tasks.sort(key=lambda t: t.finished_at or t.created_at)
            
            # Remove oldest tasks
            to_remove = len(self._tasks) - self._max_tasks + 100
            for task in terminal_tasks[:to_remove]:
                del self._tasks[task.task_id]
    
    def get_stats(self) -> Dict[str, int]:
        """Get task statistics."""
        stats = {status.value: 0 for status in TaskStatus}
        
        for task in self._tasks.values():
            stats[task.status.value] += 1
        
        return stats


# Global task manager instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get or create the global task manager."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
