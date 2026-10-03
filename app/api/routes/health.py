from fastapi import APIRouter, Response, status

from app.schemas.health import DetailedHealthResponse, HealthResponse
from app.services.health_service import HealthService

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def get_health():
    return HealthService.get_basic_health()

@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def get_detailed_health(response: Response):
    health_data = await HealthService.get_detailed_health()
    if health_data["status"] != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return health_data
