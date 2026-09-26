from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AccountCreate(BaseModel):
    bank_name: str
    account_type: str
    last_four: str


class TransactionCreate(BaseModel):
    account_id: int
    posted_date: date
    description: str
    amount: float
    merchant: Optional[str] = None
    category: Optional[str] = "Uncategorized"
    subcategory: Optional[str] = None
    source: Optional[str] = "vllm_inference"


class Transaction(TransactionCreate):
    transaction_id: int

    model_config = ConfigDict(from_attributes=True)