"""
API v1 Main Router
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.catalogue import router as catalogue_router
from app.api.v1.documents import router as documents_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.search import router as search_router
from app.api.v1.syllabus import router as syllabus_router
from app.api.v1.stats import router as stats_router
from app.api.v1.moderation import router as moderation_router
from app.api.v1.chat import router as chat_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(catalogue_router)
api_router.include_router(documents_router)
api_router.include_router(analysis_router)
api_router.include_router(reviews_router)
api_router.include_router(search_router)
api_router.include_router(syllabus_router)
api_router.include_router(stats_router)
api_router.include_router(moderation_router)
api_router.include_router(chat_router)

@api_router.get("/status")
async def api_status():
    return {"version": "v1", "status": "online"}
