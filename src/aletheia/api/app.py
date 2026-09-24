"""FastAPI application factory for Aletheia."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aletheia.api.routes.health import router as health_router
from aletheia.api.routes.investigation import router as investigation_router
from aletheia.api.routes.evaluation import router as evaluation_router
from aletheia.config.settings import get_settings
from aletheia.observability.logging import setup_logging
from aletheia.observability.metrics import metrics_router
from aletheia.observability.middleware import ObservabilityMiddleware
from aletheia.observability.tracing import setup_tracing


def create_app() -> FastAPI:
    """Create and configure an instance of the Aletheia FastAPI application."""
    settings = get_settings()

    # Initialize observability subsystems
    setup_logging(service_name="aletheia-api", log_level=settings.aletheia_log_level)
    setup_tracing(service_name="aletheia-api", enable_in_memory=True)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Aletheia: AI-Powered Incident Investigation Platform",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Observability middleware captures correlation IDs, metrics, and OpenTelemetry spans
    app.add_middleware(ObservabilityMiddleware, service_name="aletheia-api")

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
    app.include_router(metrics_router)
    app.include_router(investigation_router)
    app.include_router(evaluation_router)

    return app


app = create_app()
