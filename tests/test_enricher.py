import pytest
from unittest.mock import AsyncMock
from ledgerly.pipeline.enricher import TransactionEnricher
from ledgerly.inference.schema import EnrichmentResponse


@pytest.mark.asyncio
async def test_enricher_vllm_success():
    """Tests that enricher correctly uses vLLM classification when available."""
    mock_vllm = AsyncMock()
    mock_vllm.classify_transaction.return_value = EnrichmentResponse(
        merchant="Spotify",
        category="Shopping",
        subcategory="Subscriptions & Software",
    )

    enricher = TransactionEnricher(vllm_client=mock_vllm)

    result = await enricher.enrich(
        description="VISA DDA PUR AP SPOTIFY 877 778 1161",
        amount=-21.31,
        account_type="Checking",
    )

    assert result["merchant"] == "Spotify"
    assert result["category"] == "Shopping"
    assert result["subcategory"] == "Subscriptions & Software"
    assert result["source"] == "vllm_inference"
    mock_vllm.classify_transaction.assert_called_once()


@pytest.mark.asyncio
async def test_enricher_fallback_on_error():
    """Tests that enricher safely falls back when vLLM fails or throws an exception."""
    mock_vllm = AsyncMock()
    mock_vllm.classify_transaction.side_effect = Exception("Connection refused")

    enricher = TransactionEnricher(vllm_client=mock_vllm)

    result = await enricher.enrich(
        description="UNKNOWN MERCHANT 123",
        amount=-50.00,
        account_type="Checking",
    )

    assert result["merchant"] == "UNKNOWN MERCHANT 123"
    assert result["category"] == "Uncategorized"
    assert result["subcategory"] == "Other"
    assert result["source"] == "fallback"