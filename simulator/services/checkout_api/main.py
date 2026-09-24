"""Main application entry point for the simulated Checkout API."""

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from simulator.services.checkout_api.config import get_checkout_settings
from simulator.services.checkout_api.database import init_db, get_session_factory, get_engine
from simulator.services.checkout_api.routes import router
from simulator.services.checkout_api.seed import seed_initial_data

# Configure structured logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
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

    app = FastAPI(
        title=f"Simulated Production: {settings.service_name}",
        version=settings.service_version,
        description="Simulated eCommerce Checkout Service for Aletheia Incident Investigation",
        lifespan=lifespan,
    )

    # Middleware for request timing and audit logging
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} -> "
            f"status={response.status_code} duration={duration_ms}ms"
        )
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
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
