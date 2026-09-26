import asyncio
from typing import Any, Dict, Optional
import logging

from ledgerly.inference.schema import EnrichmentResponse
from ledgerly.inference.vllm_client import VLLMClient
from ledgerly.pipeline.cleaner import clean_description_for_llm

logger = logging.getLogger(__name__)


class TransactionEnricher:
    """Pure LLM-driven enrichment engine using local vLLM for zero-maintenance classification."""

    def __init__(self, vllm_client: Optional[VLLMClient] = None, max_concurrency: int = 8):
        self.vllm_client = vllm_client or VLLMClient()
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def enrich(
        self, description: str, amount: float, account_type: str = "Checking"
    ) -> Dict[str, Any]:
        
        # Clean description specifically for LLM consumption
        llm_input_desc = clean_description_for_llm(description)
        
        # (Optional debug log to see what the LLM actually receives)
        logger.debug(f"Raw: '{description}' -> Cleaned for LLM: '{llm_input_desc}'")

        # ... [Deterministic Overrides Check using description or llm_input_desc] ...

        # 2. Direct Local vLLM Inference using the CLEANED description
        try:
            async with self.semaphore:
                response: Optional[EnrichmentResponse] = (
                    await self.vllm_client.classify_transaction(
                        description=llm_input_desc,
                        amount=amount,
                        account_type=account_type,
                    )
                )

            if response:
                merchant = response.merchant
                if merchant.lower() in ["uncleaned merchant name", "unknown merchant", "uncategorized"]:
                    merchant = llm_input_desc  # Fallback to cleaned text if LLM fumbles

                return {
                    "merchant": merchant,
                    "category": response.category,
                    "subcategory": response.subcategory,
                    "source": "vllm_inference",
                }
        except Exception as e:
            logger.error(f"vLLM Inference failed for '{description}': {e}")

        # Fallback if vLLM fails
        return {
            "merchant": description,
            "category": "Uncategorized",
            "subcategory": "Other",
            "source": "fallback",
        }