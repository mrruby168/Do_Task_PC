"""
PC Tool Server - Database Module

SQLite database setup and session management using SQLAlchemy.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_config


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager."""
        config = get_config()
        self.database_url = database_url or config.DATABASE_URL
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[async_sessionmaker] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database engine and session maker."""
        if self._initialized:
            return
        
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            future=True,
        )
        
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        self._initialized = True
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self._initialized:
            self.initialize()
        
        assert self.engine is not None
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if not self._initialized:
            self.initialize()
        
        assert self.async_session_maker is not None
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async for session in db_manager.get_session():
        yield session


async def init_db() -> None:
    """Initialize database and create tables."""
    db_manager.initialize()
    await db_manager.create_tables()
