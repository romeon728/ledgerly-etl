from typing import Literal, Optional, get_args, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

# Master Taxonomy Definitions
CategoryType = Literal[
    "Housing",
    "Transportation",
    "Food & Dining",
    "Shopping",
    "Utilities & Bills",
    "Entertainment",
    "Income",
    "Financial & Transfers",
    "Healthcare",
    "Uncategorized",
]

SubcategoryType = Literal[
    "Groceries",
    "Restaurants & Coffee",
    "Automotive & Fuel",
    "Public Transit & Rideshare",
    "Subscriptions & Software",
    "General Retail",
    "Payroll & Direct Deposit",
    "Account Transfer",
    "Utilities",
    "Rent & Mortgage",
    "Medical & Pharmacy",
    "Other",
]

# Exported tuple list for prompt building
ALLOWED_CATEGORIES = get_args(CategoryType)
ALLOWED_SUBCATEGORIES = get_args(SubcategoryType)


class EnrichmentResponse(BaseModel):
    """Schema returned by local vLLM guided output."""

    merchant: str = Field(
        ...,
        description="Cleaned, human-readable merchant name.",
    )
    category: CategoryType = Field(
        ...,
        description="Standardized primary category.",
    )
    subcategory: Optional[SubcategoryType] = Field(
        None,
        description="Standardized subcategory.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_incoming_json(cls, data: Any) -> Any:
        """Pre-processes raw JSON dict keys and string nulls before field validation."""
        if not isinstance(data, dict):
            return data

        normalized = {}
        for key, val in data.items():
            k_clean = key.lower().replace("_", "").strip()

            # Convert string representations of null/none to Python None
            if isinstance(val, str) and val.strip().lower() in ("none", "null", "n/a", "undefined", ""):
                val = None

            # Route fuzzy key variations to standard schema keys
            if "merchant" in k_clean:
                normalized["merchant"] = val
            elif "sub" in k_clean or "subcategory" in k_clean:
                normalized["subcategory"] = val
            elif "category" in k_clean:
                normalized["category"] = val
            else:
                normalized[key] = val

        return normalized

    @field_validator("merchant", mode="before")
    @classmethod
    def fallback_empty_merchant(cls, v: Any) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            return "Unknown Merchant"
        return v.strip()

    @field_validator("category", mode="before")
    @classmethod
    def validate_and_fallback_category(cls, v: Any) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            return "Uncategorized"

        val_clean = v.strip()

        # Dynamic case-insensitive match against allowed CategoryType options
        for allowed in ALLOWED_CATEGORIES:
            if val_clean.lower() == allowed.lower():
                return allowed

        # Keyword hints for common LLM category variations
        val_lower = val_clean.lower()
        if "transfer" in val_lower or "xfer" in val_lower or "payment" in val_lower:
            return "Financial & Transfers"
        if "income" in val_lower or "deposit" in val_lower or "payroll" in val_lower:
            return "Income"
        if "uber" in val_lower or "ride" in val_lower or "transit" in val_lower:
            return "Transportation"

        return "Uncategorized"

    @field_validator("subcategory", mode="before")
    @classmethod
    def validate_and_fallback_subcategory(cls, v: Any) -> Optional[str]:
        if not v or not isinstance(v, str) or not v.strip():
            return None

        val_clean = v.strip()

        # Dynamic case-insensitive match against allowed SubcategoryType options
        for allowed in ALLOWED_SUBCATEGORIES:
            if val_clean.lower() == allowed.lower():
                return allowed

        # Keyword hints for common subcategories
        val_lower = val_clean.lower()
        if "transfer" in val_lower or "xfer" in val_lower or "zelle" in val_lower:
            return "Account Transfer"
        if "stream" in val_lower or "software" in val_lower or "music" in val_lower:
            return "Subscriptions & Software"
        if "uber" in val_lower or "lyft" in val_lower or "trip" in val_lower:
            return "Public Transit & Rideshare"

        return "Other"