from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.demo import router as demo_router
from app.api.health import router as health_router
from app.api.instruments import router as instruments_router
from app.api.market import router as market_router
from app.api.watchlists import router as watchlists_router
from app.config import get_settings
from app.domain.errors import DomainError
from app.schemas.common import ApiErrorEnvelope

settings = get_settings()
app = FastAPI(title="Smart Market Watchlist API", version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def error_response(
    status_code: int, code: str, message: str, details: dict | None = None
) -> JSONResponse:
    payload = ApiErrorEnvelope(error={"code": code, "message": message, "details": details})
    return JSONResponse(status_code=status_code, content=payload.model_dump(exclude_none=True))


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    details = exc.detail if isinstance(exc.detail, dict) else None
    return error_response(exc.status_code, "http_error", message, details)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    details = exc.detail if isinstance(exc.detail, dict) else None
    return error_response(exc.status_code, "http_error", message, details)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        422, "validation_error", "Request validation failed.", {"issues": exc.errors()}
    )


@app.exception_handler(DomainError)
async def domain_exception_handler(_: Request, exc: DomainError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, str(exc))


@app.exception_handler(Exception)
async def unexpected_exception_handler(_: Request, __: Exception) -> JSONResponse:
    return error_response(500, "internal_error", "An unexpected server error occurred.")


app.include_router(health_router, prefix="/api/v1")
app.include_router(demo_router, prefix="/api/v1")
app.include_router(instruments_router, prefix="/api/v1")
app.include_router(market_router, prefix="/api/v1")
app.include_router(watchlists_router, prefix="/api/v1")
