"""Health check endpoints for Aletheia platform."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from aletheia.config.settings import Settings, get_settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response payload."""
    status: str
    service: str
    version: str
    environment: str
    timestamp: str


@router.get("/health", response_model=HealthResponse)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return health status of the Aletheia platform API."""
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.aletheia_env,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
