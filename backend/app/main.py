import sys
from pathlib import Path

# Ensure both backend directory and project root directory are in sys.path
_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent
_root_dir = _backend_dir.parent

if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

try:
    from app.core.config import settings
    from app.core.logging import logger
    from app.api.v1.router import api_router
    from app.db.base import Base
    from app.db.session import engine
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.logging import logger
    from backend.app.api.v1.router import api_router
    from backend.app.db.base import Base
    from backend.app.db.session import engine

# Create tables for local fallback (SQLite)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Standardized Error Payload Handler for Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request payload parameters",
                "details": exc.errors()
            }
        }
    )

# Standardized Global Unhandled Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {}
            }
        }
    )

# Include Versioned API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "success": True,
        "message": f"Welcome to {settings.APP_NAME} API Service",
        "health_check": f"{settings.API_V1_STR}/health",
        "docs": "/docs"
    }
