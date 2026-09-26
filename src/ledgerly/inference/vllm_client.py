from typing import Optional
import httpx
from pydantic import ValidationError

from ledgerly.config import settings
from ledgerly.inference.prompts import build_system_prompt, build_user_prompt
from ledgerly.inference.schema import EnrichmentResponse


class VLLMClient:
    """Async client connecting to local vLLM instance running on host/container."""

    def __init__(self):
        self.base_url = settings.vllm_base_url.rstrip("/")
        self.model = settings.vllm_model_name

    async def classify_transaction(
        self, description: str, amount: float, account_type: str = "Checking"
    ) -> Optional[EnrichmentResponse]:
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(description, amount, account_type)
        schema = EnrichmentResponse.model_json_schema()

        print("==================================================")
        print(user_prompt)
        print("--------------------------------------------------")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,  # Zero temperature for deterministic classification
            "guided_json": schema,  # Native vLLM guided decoding handles everything
        }

        # Resolve endpoint path cleanly
        endpoint = self.base_url
        if not endpoint.endswith("/chat/completions"):
            endpoint = f"{endpoint}/v1/chat/completions" if not endpoint.endswith("/v1") else f"{endpoint}/chat/completions"

        async with httpx.AsyncClient(timeout=30.0) as client:
            raw_content = ""
            try:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()

                raw_content = data["choices"][0]["message"]["content"]
                print(raw_content)
                print("==================================================")
                return EnrichmentResponse.model_validate_json(raw_content)

            except httpx.HTTPStatusError as exc:
                print(f"❌ vLLM HTTP {exc.response.status_code} Error for '{description}': {exc.response.text}")
                return None
            except httpx.RequestError as exc:
                print(f"❌ vLLM Connection Failed for '{description}': {exc}")
                return None
            except ValidationError as exc:
                print(
                    f"❌ Validation Error for '{description}':\n"
                    f"   Raw vLLM Output: {raw_content}\n"
                    f"   Details: {exc}"
                )
                return None
            except Exception as exc:
                print(f"❌ Unexpected Error classifying '{description}': {exc}")
                return None