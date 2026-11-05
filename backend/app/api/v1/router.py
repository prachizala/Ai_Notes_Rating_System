"""
API v1 Main Router
"""

from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/status")
async def api_status():
    return {"version": "v1", "status": "online"}
