import pytest
from ledgerly.inference.prompts import build_user_prompt
from ledgerly.inference.schema import EnrichmentResponse


def test_build_user_prompt_from_raw_csv_row():
    # Simulating a raw, unclean row straight out of your bank export
    raw_csv_description = (
        "VISA DDA PUR AP 403629  SPOTIFY             877 778 1161 * NY"
    )
    raw_amount = -21.31

    prompt = build_user_prompt(
        description=raw_csv_description,
        amount=raw_amount,
        account_type="Checking",
    )

    assert "VISA DDA PUR AP 403629  SPOTIFY" in prompt
    assert "-21.31" in prompt


@pytest.mark.asyncio
async def test_vllm_schema_validation():
    # Validates that JSON structured responses conform strictly to our schema
    sample_json = '{"merchant": "Spotify", "category": "Shopping", "subcategory": "Subscriptions & Software"}'
    parsed = EnrichmentResponse.model_validate_json(sample_json)

    assert parsed.merchant == "Spotify"
    assert parsed.category == "Shopping"
    assert parsed.subcategory == "Subscriptions & Software"