"""
API v1 Main Router
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.catalogue import router as catalogue_router
from app.api.v1.documents import router as documents_router
from app.api.v1.analysis import router as analysis_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(catalogue_router)
api_router.include_router(documents_router)
api_router.include_router(analysis_router)

@api_router.get("/status")
async def api_status():
    return {"version": "v1", "status": "online"}
