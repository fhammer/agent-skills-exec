"""健康检查路由"""

from fastapi import APIRouter, Depends
from datetime import datetime
from api.schemas import HealthResponse
from api.database import get_session

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        database="connected",
        redis="connected"
    )


@router.get("/ping")
async def ping():
    """简单 ping"""
    return {"pong": True}
