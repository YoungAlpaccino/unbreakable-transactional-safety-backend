from fastapi import APIRouter
from app.api.submit import router as submit_router

api_router = APIRouter()
api_router.include_router(submit_router, prefix="/submit", tags=["submit"])
