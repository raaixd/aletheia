"""FastAPI application factory for Aletheia."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aletheia.api.routes.health import router as health_router
from aletheia.config.settings import get_settings


def create_app() -> FastAPI:
    """Create and configure an instance of the Aletheia FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Aletheia: AI-Powered Incident Investigation Platform",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Enable CORS for local development and future UI integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router)

    return app


app = create_app()
