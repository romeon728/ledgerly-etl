from typing import Literal, Optional
from pydantic import BaseModel, Field

# Pre-defined Taxonomy Enums to maintain strict consistency
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


class EnrichmentResponse(BaseModel):
    """Schema returned by local vLLM guided output."""

    merchant: str = Field(
        ...,
        description="Cleaned, human-readable merchant name (e.g., 'Spotify' from 'VISA DDA PUR AP SPOTIFY').",
    )
    category: CategoryType = Field(
        ..., description="Standardized primary category."
    )
    subcategory: Optional[SubcategoryType] = Field(
        None, description="Standardized subcategory."
    )