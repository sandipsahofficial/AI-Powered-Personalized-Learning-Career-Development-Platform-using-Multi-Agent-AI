import logging
from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create asynchronous engine for PostgreSQL
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_size=settings.POSTGRES_POOL_SIZE,
    max_overflow=settings.POSTGRES_MAX_OVERFLOW,
    pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> Dict[str, Any]:
    """
    Executes a direct health query and checks for pgvector extension presence.
    """
    try:
        async with engine.connect() as conn:
            # Check basic connectivity
            result = await conn.execute(text("SELECT 1;"))
            scalar = result.scalar()
            
            # Check for pgvector extension
            ext_result = await conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
            )
            vector_version = ext_result.scalar()

            # Check database name
            db_name_result = await conn.execute(text("SELECT current_database();"))
            current_db = db_name_result.scalar()

            return {
                "status": "healthy" if scalar == 1 else "unhealthy",
                "database": current_db,
                "pgvector_installed": vector_version is not None,
                "pgvector_version": vector_version or "Not Enabled",
                "pool_size": settings.POSTGRES_POOL_SIZE
            }
    except Exception as e:
        logger.warning(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": settings.POSTGRES_DB,
            "pgvector_installed": False
        }
