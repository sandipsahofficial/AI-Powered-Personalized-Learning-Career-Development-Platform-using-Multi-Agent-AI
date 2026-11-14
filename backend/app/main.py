from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler
)
from app.api.v1.api import api_router
from app.db.redis import redis_manager

# Initialize structured logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    logger.info(f"Connecting to database at {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    logger.info(f"Configured Ollama endpoint at {settings.OLLAMA_BASE_URL}")

    # Seed canonical taxonomy and resources on startup
    try:
        from app.db.session import AsyncSessionLocal
        from app.services.career_seeder import CareerSeeder
        async with AsyncSessionLocal() as db:
            await CareerSeeder.seed_career_data(db)
            logger.info("Startup career taxonomy and learning resources verified.")
    except Exception as e:
        logger.warning(f"Startup database seeding notice: {e}")

    yield
    # Shutdown actions
    logger.info("Shutting down application resources...")
    await redis_manager.close()
    logger.info("Redis client connections closed cleanly.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for AI-Powered Personalized Learning & Career Development Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
