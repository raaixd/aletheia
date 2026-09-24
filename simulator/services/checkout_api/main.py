"""Main application entry point for the simulated Checkout API."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aletheia.observability.logging import setup_logging
from aletheia.observability.metrics import metrics_router
from aletheia.observability.middleware import ObservabilityMiddleware
from aletheia.observability.tracing import setup_tracing
from simulator.services.checkout_api.config import get_checkout_settings
from simulator.services.checkout_api.database import init_db, get_session_factory, get_engine
from simulator.services.checkout_api.routes import router
from simulator.services.checkout_api.seed import seed_initial_data

logger = logging.getLogger("checkout-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown lifecycle."""
    logger.info("Starting Checkout API service...")
    try:
        init_db()
        session_factory = get_session_factory()
        with session_factory() as db:
            seeded = seed_initial_data(db)
            if seeded > 0:
                logger.info(f"Initialized database with {seeded} catalog products.")
        logger.info("Database initialization and verification complete.")
    except Exception as exc:
        logger.warning(
            f"Could not connect to database on startup: {exc}. "
            "Database might still be starting or using mock in test mode."
        )

    yield

    logger.info("Shutting down Checkout API service...")
    settings = get_checkout_settings()
    if settings.service_environment != "test":
        from simulator.services.checkout_api import database
        if database._engine is not None:
            database._engine.dispose()
    logger.info("Checkout API shutdown complete.")


def create_checkout_app() -> FastAPI:
    """Create and configure Checkout API FastAPI application."""
    settings = get_checkout_settings()

    # Initialize observability subsystems
    setup_logging(service_name=settings.service_name)
    setup_tracing(service_name=settings.service_name, enable_in_memory=True)

    app = FastAPI(
        title=f"Simulated Production: {settings.service_name}",
        version=settings.service_version,
        description="Simulated eCommerce Checkout Service for Aletheia Incident Investigation",
        lifespan=lifespan,
    )

    # Observability middleware captures correlation IDs, Prometheus metrics, and OpenTelemetry spans
    app.add_middleware(ObservabilityMiddleware, service_name=settings.service_name)

    # Enable CORS for frontend and service-to-service communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    app.include_router(metrics_router)
    return app


app = create_checkout_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_checkout_settings()
    uvicorn.run(
        "simulator.services.checkout_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
