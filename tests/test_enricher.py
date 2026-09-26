import pytest
from ledgerly.pipeline.enricher import TransactionEnricher


@pytest.mark.asyncio
async def test_enricher_rule_engine_match():
    enricher = TransactionEnricher()
    
    # Should match rule engine for Spotify directly without calling vLLM
    result = await enricher.enrich(
        description="VISA DDA PUR AP SPOTIFY 877 778 1161",
        amount=-21.31,
        account_type="Checking",
    )

    assert result["merchant"] == "Spotify"
    assert result["category"] == "Shopping"
    assert result["source"] == "rule_engine"