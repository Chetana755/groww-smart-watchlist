from typing import Any

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ApiErrorEnvelope(BaseModel):
    error: ApiError


class HealthResponse(BaseModel):
    status: str = Field(pattern="^ok$")
    version: str
