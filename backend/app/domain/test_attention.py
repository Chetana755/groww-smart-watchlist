from app.domain.attention import AttentionLevel, calculate_attention


def test_normal_day_has_no_attention():
    result = calculate_attention(
        price_change_pct=0.35,
        volume=1_050_000,
        average_volume=1_000_000,
        sector_change_pct=0.4,
        index_change_pct=0.3,
    )

    assert result.score == 0
    assert result.level == AttentionLevel.NONE


def test_company_move_is_high_attention():
    result = calculate_attention(
        price_change_pct=4.2,
        volume=2_400_000,
        average_volume=1_000_000,
        sector_change_pct=0.4,
        index_change_pct=0.3,
        has_relevant_event=True,
    )

    assert result.score >= 75
    assert result.level == AttentionLevel.HIGH
    assert len(result.reasons) >= 3


def test_unusual_volume_gets_attention():
    result = calculate_attention(
        price_change_pct=0.8,
        volume=3_100_000,
        average_volume=1_000_000,
        sector_change_pct=0.4,
        index_change_pct=0.3,
    )

    assert result.evidence.volume_score == 20
    assert result.score >= 20


def test_relevance_is_capped():
    result = calculate_attention(
        price_change_pct=0,
        volume=1_000_000,
        average_volume=1_000_000,
        sector_change_pct=0,
        index_change_pct=0,
        user_relevance=100,
    )

    assert result.evidence.relevance_score == 15