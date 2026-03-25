from fastapi import APIRouter

from app.api.endpoints.commit import router as commit_router
from app.api.endpoints.plan import router as plan_router
from app.api.endpoints.pr import router as pr_router

api_router = APIRouter()

api_router.include_router(plan_router, prefix="/api", tags=["Plan"])
api_router.include_router(commit_router, prefix="/api", tags=["Commit"])
api_router.include_router(pr_router, prefix="/api", tags=["PR"])
