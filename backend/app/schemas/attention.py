from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.attention import AttentionLevel


class AttentionEvidenceResponse(BaseModel):
    priceScore: float
    volumeScore: float
    relativeScore: float
    volatilityScore: float
    eventScore: float
    relevanceScore: float


class AttentionResponse(BaseModel):
    symbol: str
    score: float
    level: AttentionLevel
    is_new: bool = Field(serialization_alias="isNew")
    latest_relevant_at: datetime = Field(serialization_alias="latestRelevantAt")
    reasons: list[str]
    evidence: AttentionEvidenceResponse
