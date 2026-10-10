import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.errors import (
    LoopWiseException,
    loopwise_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler
)
from app.api.routers import health, classify, feedback, materials, analytics
from app.seeds.materials import seed_materials_database
from app.seeds.demo_analytics import seed_demo_analytics_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("loopwise")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown initialization."""
    logger.info(f"Starting LoopWise API in {settings.ENVIRONMENT} mode (DEMO_MODE={settings.DEMO_MODE})")
    
    # Attempt DB seed initialization (graceful skip if DB is offline)
    try:
        await seed_materials_database()
        await seed_demo_analytics_database()
    except Exception as e:
        logger.warning(f"Startup DB seed attempt skipped: {e}")
        
    yield
    logger.info("Shutting down LoopWise API")


app = FastAPI(
    title="LoopWise API",
    description="Waste Segregation and Circular-Economy Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(LoopWiseException, loopwise_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Register API Routers under /api/v1
app.include_router(health.router, prefix="/api/v1")
app.include_router(classify.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(materials.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "LoopWise API",
        "tagline": "Every Waste Item Has a Next Life",
        "version": "0.1.0",
        "demo_mode": settings.DEMO_MODE,
        "docs": "/docs"
    }
