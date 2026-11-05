"""
API v1 Main Router
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router

api_router = APIRouter()

api_router.include_router(auth_router)

@api_router.get("/status")
async def api_status():
    return {"version": "v1", "status": "online"}
