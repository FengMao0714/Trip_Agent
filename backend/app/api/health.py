"""Health check API routes."""

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.models.schemas import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return the backend health status."""
    services = {
        "database": "not_configured",
        "redis": "not_configured",
        "llm": "configured" if settings.deepseek_api_key else "not_configured",
    }
    return HealthResponse(status="ok", services=services)
