"""
PC Tool Server - Main Entry Point

Ứng dụng PC Tool với kiến trúc Clean Architecture:
- FastAPI Backend (REST API)
- PySide6 GUI (Dark Theme)
- Security Gateway (7 bước validation)
- Tool System (Auto-discovery + Sandbox)

Author: Do_Task_PC Team
Version: 1.0.0
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional

# Thêm thư mục gốc vào path để import các module app
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import cấu hình
from app.config import settings

# Import database
from app.database import init_db

# Import API routers
from app.api.health import router as health_router
from app.api.tools import router as tools_router
from app.api.tasks import router as tasks_router
from app.api.approvals import router as approvals_router
from app.api.system import router as system_router
from app.api.logs import router as logs_router

# Import GUI (sẽ khởi tạo nếu không phải server mode)
try:
    from app.gui.main_window import MainWindow
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QThread, Signal
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False

# Cấu hình logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ROOT_DIR / 'logs' / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ServerThread(QThread):
    """Thread chạy FastAPI server trong nền khi có GUI"""
    started = Signal()
    stopped = Signal()
    
    def __init__(self, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port
        self._should_stop = False
    
    def run(self):
        """Chạy UVICorn server trong thread riêng"""
        config = uvicorn.Config(
            app=create_app(),
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False
        )
        server = uvicorn.Server(config)
        
        self.started.emit()
        logger.info(f"Server started on http://{self.host}:{self.port}")
        
        # Chạy server trong thread này
        asyncio.run(server.serve())
        
        self.stopped.emit()
    
    def stop(self):
        """Dừng server một cách graceful"""
        self._should_stop = True


def create_app() -> FastAPI:
    """
    Tạo và cấu hình FastAPI application
    
    Returns:
        FastAPI: Application instance đã được cấu hình đầy đủ
    """
    app = FastAPI(
        title="PC Tool Server",
        description="Hệ thống thực thi tool tự động với bảo mật cao",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # Cấu hình CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(health_router, prefix="/api/health", tags=["Health"])
    app.include_router(tools_router, prefix="/api/tools", tags=["Tools"])
    app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
    app.include_router(approvals_router, prefix="/api/approvals", tags=["Approvals"])
    app.include_router(system_router, prefix="/api/system", tags=["System"])
    app.include_router(logs_router, prefix="/api/logs", tags=["Logs"])
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Khởi tạo database và các service khi app start"""
        logger.info("Starting up PC Tool Server...")
        await init_db()
        logger.info("Database initialized successfully")
        
        # TODO: Khởi tạo Tool Registry
        # TODO: Khởi tạo Task Manager
        # TODO: Khởi tạo Approval Manager
        
        logger.info("All services started successfully")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Dọn dẹp resources khi app shutdown"""
        logger.info("Shutting down PC Tool Server...")
        # TODO: Đóng kết nối database
        # TODO: Dừng các task đang chạy
        logger.info("Shutdown complete")
    
    return app


def run_server_only(host: str = settings.HOST, port: int = settings.PORT):
    """
    Chạy chỉ FastAPI server (không có GUI)
    
    Args:
        host: Host address để bind
        port: Port để lắng nghe
    """
    logger.info(f"Starting server-only mode on {host}:{port}")
    uvicorn.run(
        "app.main:create_app",
        host=host,
        port=port,
        log_level="info",
        reload=settings.DEBUG
    )


def run_gui_with_server(host: str = settings.HOST, port: int = settings.PORT):
    """
    Chạy GUI PySide6 kèm theo FastAPI server trong nền
    
    Args:
        host: Host address cho server
        port: Port cho server
    """
    if not HAS_PYSIDE6:
        logger.error("PySide6 not available. Falling back to server-only mode.")
        run_server_only(host, port)
        return
    
    logger.info("Starting GUI with embedded server...")
    
    app_qt = QApplication(sys.argv)
    app_qt.setApplicationName("PC Tool Server")
    
    # Tạo và start server thread
    server_thread = ServerThread(host, port)
    server_thread.start()
    
    # Tạo main window
    window = MainWindow(server_thread=server_thread)
    window.show()
    
    # Event loop của Qt
    exit_code = app_qt.exec()
    
    # Dừng server trước khi thoát
    server_thread.stop()
    server_thread.wait(5000)  # Wait tối đa 5 giây
    
    sys.exit(exit_code)


def main():
    """
    Entry point chính của ứng dụng
    
    Chế độ chạy được xác định bởi argument hoặc environment variable:
    - --server-only: Chỉ chạy FastAPI server
    - --gui (mặc định): Chạy GUI kèm server trong nền
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="PC Tool Server")
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Chỉ chạy FastAPI server (không có GUI)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.HOST,
        help=f"Host address (default: {settings.HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.PORT,
        help=f"Port number (default: {settings.PORT})"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Chạy GUI kèm server (chế độ mặc định)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.server_only or (not args.gui and not HAS_PYSIDE6):
            run_server_only(args.host, args.port)
        else:
            run_gui_with_server(args.host, args.port)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Shutting down...")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
