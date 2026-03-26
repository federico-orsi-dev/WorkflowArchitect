from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status

from app.api.router import api_router
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RateLimitMiddleware, RequestIdMiddleware
from app.core.settings import settings

load_dotenv()

configure_logging(settings.log_level)
logger = get_logger()

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    openapi_tags=[
        {
            "name": "Plan",
            "description": "MicroPlanner endpoints for creating execution-ready plans.",
        },
        {
            "name": "Commit",
            "description": "CommitSense endpoints for refining summaries and commit messages.",
        },
        {
            "name": "Meta",
            "description": "Service metadata and health checks.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
app.add_middleware(RequestIdMiddleware)

app.include_router(api_router)


@app.get(
    "/health",
    tags=["Meta"],
    summary="Health check",
    description="Returns ok if the service is up.",
)
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
