from typing import Optional
import httpx
from ledgerly.config import settings
from ledgerly.inference.prompts import SYSTEM_PROMPT, build_user_prompt
from ledgerly.inference.schema import EnrichmentResponse


class VLLMClient:
    """Async client connecting to local vLLM instance running on host/container."""

    def __init__(self):
        self.base_url = settings.vllm_base_url.rstrip("/")
        self.model = settings.vllm_model_name

    async def classify_transaction(
        self, description: str, amount: float, account_type: str = "Checking"
    ) -> Optional[EnrichmentResponse]:
        user_prompt = build_user_prompt(description, amount, account_type)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,  # Zero temperature for deterministic classification
            "response_format": {
                "type": "json_object",
                "schema": EnrichmentResponse.model_json_schema(),
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", json=payload
            )
            response.raise_for_status()
            data = response.json()

            raw_content = data["choices"][0]["message"]["content"]
            return EnrichmentResponse.model_validate_json(raw_content)