from dataclasses import dataclass
from enum import StrEnum


class AttentionLevel(StrEnum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class AttentionEvidence:
    price_score: float
    volume_score: float
    relative_score: float
    volatility_score: float
    event_score: float
    relevance_score: float


@dataclass(frozen=True)
class AttentionResult:
    score: float
    level: AttentionLevel
    evidence: AttentionEvidence
    reasons: tuple[str, ...]


def calculate_attention(
    *,
    price_change_pct: float,
    volume: float,
    average_volume: float,
    sector_change_pct: float,
    index_change_pct: float,
    has_relevant_event: bool = False,
    user_relevance: float = 0.0,
    volatility_pct: float = 0.0,
) -> AttentionResult:

    # Price anomaly: max 20
    abs_price = abs(price_change_pct)

    if abs_price >= 5:
        price_score = 20
    elif abs_price >= 3:
        price_score = 15
    elif abs_price >= 1.5:
        price_score = 8
    else:
        price_score = 0

    # Volume anomaly: max 20
    volume_ratio = volume / average_volume if average_volume > 0 else 0

    if volume_ratio >= 3:
        volume_score = 20
    elif volume_ratio >= 2:
        volume_score = 15
    elif volume_ratio >= 1.5:
        volume_score = 8
    else:
        volume_score = 0

    # Relative movement: max 15
    relative_move = abs(price_change_pct - sector_change_pct)

    if relative_move >= 4:
        relative_score = 15
    elif relative_move >= 2:
        relative_score = 10
    elif relative_move >= 1:
        relative_score = 5
    else:
        relative_score = 0

    # Volatility: max 10
    abs_volatility = abs(volatility_pct)

    if abs_volatility >= 5:
        volatility_score = 10
    elif abs_volatility >= 3:
        volatility_score = 7
    elif abs_volatility >= 1.5:
        volatility_score = 4
    else:
        volatility_score = 0

    # Event: max 20
    event_score = 20 if has_relevant_event else 0

    # User relevance: max 15
    relevance_score = max(0, min(15, user_relevance))

    score = min(
        100,
        price_score
        + volume_score
        + relative_score
        + volatility_score
        + event_score
        + relevance_score,
    )

    if score >= 75:
        level = AttentionLevel.HIGH
    elif score >= 50:
        level = AttentionLevel.MODERATE
    elif score >= 25:
        level = AttentionLevel.LOW
    else:
        level = AttentionLevel.NONE

    reasons: list[str] = []

    if price_score:
        reasons.append(f"Price moved {price_change_pct:+.1f}%")

    if volume_score:
        reasons.append(f"Volume is {volume_ratio:.1f}x average")

    if relative_score:
        reasons.append(
            f"Moved {relative_move:.1f}% relative to sector"
        )

    if volatility_score:
        reasons.append(f"Volatility is {volatility_pct:.1f}%")

    if event_score:
        reasons.append("Relevant company event detected")

    if relevance_score:
        reasons.append("Matches your watchlist interest")

    return AttentionResult(
        score=round(score, 2),
        level=level,
        evidence=AttentionEvidence(
            price_score=price_score,
            volume_score=volume_score,
            relative_score=relative_score,
            volatility_score=volatility_score,
            event_score=event_score,
            relevance_score=relevance_score,
        ),
        reasons=tuple(reasons),
    )