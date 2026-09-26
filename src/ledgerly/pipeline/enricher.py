from typing import Dict, Any, Optional
from ledgerly.inference.vllm_client import VLLMClient
from ledgerly.inference.schema import EnrichmentResponse


class TransactionEnricher:
    """Hybrid enrichment engine combining deterministic rule matching with local vLLM fallback."""

    def __init__(self, vllm_client: Optional[VLLMClient] = None):
        self.vllm_client = vllm_client or VLLMClient()

    async def enrich(
        self, description: str, amount: float, account_type: str = "Checking"
    ) -> Dict[str, Any]:
        """Attempts fast rule-based classification before querying local vLLM."""
        
        # 1. Fast Deterministic Rules Engine (Examples / Pre-filtering)
        clean_desc = description.upper()
        
        if "SPOTIFY" in clean_desc:
            return {
                "merchant": "Spotify",
                "category": "Shopping",
                "subcategory": "Subscriptions & Software",
                "source": "rule_engine",
            }
        
        if "DIRECT DEP" in clean_desc or "PAYROLL" in clean_desc:
            return {
                "merchant": "Payroll / Employer",
                "category": "Income",
                "subcategory": "Payroll & Direct Deposit",
                "source": "rule_engine",
            }

        # 2. Local vLLM Inference Fallback for Unmatched Transactions
        try:
            response: Optional[EnrichmentResponse] = await self.vllm_client.classify_transaction(
                description=description,
                amount=amount,
                account_type=account_type
            )
            
            if response:
                return {
                    "merchant": response.merchant,
                    "category": response.category,
                    "subcategory": response.subcategory,
                    "source": "vllm_inference",
                }
        except Exception as e:
            # Fallback guard if vLLM server is unreachable or errors out
            pass

        return {
            "merchant": description,
            "category": "Uncategorized",
            "subcategory": "Other",
            "source": "fallback",
        }