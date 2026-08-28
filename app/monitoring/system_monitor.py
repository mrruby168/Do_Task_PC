"""
PC Tool Server - System Monitor

Real-time system monitoring for CPU, RAM, GPU, and storage.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import psutil


logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitors system resources."""
    
    def __init__(self):
        """Initialize system monitor."""
        self._start_time = datetime.utcnow()
        self._request_count = 0
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information."""
        try:
            usage = psutil.cpu_percent(interval=0.1)
            freq = psutil.cpu_freq()
            
            return {
                "usage_percent": usage,
                "frequency_mhz": freq.current if freq else 0,
                "cores": psutil.cpu_count(logical=False) or 0,
                "logical_cores": psutil.cpu_count() or 0,
            }
        except Exception as e:
            logger.error(f"Failed to get CPU info: {e}")
            return {"usage_percent": 0, "error": str(e)}
    
    def get_ram_info(self) -> Dict[str, Any]:
        """Get RAM information."""
        try:
            mem = psutil.virtual_memory()
            
            return {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "usage_percent": mem.percent,
            }
        except Exception as e:
            logger.error(f"Failed to get RAM info: {e}")
            return {"total_gb": 0, "error": str(e)}
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information."""
        try:
            # Try to use pynvml for NVIDIA GPUs
            import pynvml
            
            try:
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                
                gpu_name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(gpu_name, bytes):
                    gpu_name = gpu_name.decode('utf-8')
                
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                pynvml.nvmlShutdown()
                
                return {
                    "name": gpu_name,
                    "memory_total_mb": memory_info.total // (1024**2),
                    "memory_used_mb": memory_info.used // (1024**2),
                    "memory_free_mb": memory_info.free // (1024**2),
                    "usage_percent": gpu_util.gpu,
                    "memory_percent": round(
                        (memory_info.used / memory_info.total) * 100, 2
                    ),
                }
            except Exception:
                # No NVIDIA GPU or error
                return {
                    "name": "Not available",
                    "memory_total_mb": 0,
                    "memory_used_mb": 0,
                    "usage_percent": 0,
                }
                
        except ImportError:
            # pynvml not installed
            return {
                "name": "Not available (pynvml not installed)",
                "memory_total_mb": 0,
                "usage_percent": 0,
            }
        except Exception as e:
            logger.error(f"Failed to get GPU info: {e}")
            return {"name": "Error", "error": str(e)}
    
    def get_storage_info(self, path: str = "/") -> Dict[str, Any]:
        """Get storage information."""
        try:
            usage = psutil.disk_usage(path)
            
            return {
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "usage_percent": usage.percent,
            }
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return {"total_gb": 0, "error": str(e)}
    
    def increment_request_count(self) -> None:
        """Increment request counter."""
        self._request_count += 1
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server status information."""
        uptime = datetime.utcnow() - self._start_time
        
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "status": "ONLINE",
            "uptime": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "requests": self._request_count,
            "start_time": self._start_time.isoformat(),
        }
    
    def get_all_info(self) -> Dict[str, Any]:
        """Get all system information."""
        return {
            "cpu": self.get_cpu_info(),
            "ram": self.get_ram_info(),
            "gpu": self.get_gpu_info(),
            "storage": self.get_storage_info(),
            "server": self.get_server_info(),
        }


# Global monitor instance
_system_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """Get or create the global system monitor."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor
