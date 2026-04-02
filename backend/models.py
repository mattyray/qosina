"""Pydantic models for request/response validation."""

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_case: Optional[str] = "general"  # "general", "sales_orders", "ap_processing", "product_data"


class ApprovalUpdate(BaseModel):
    status: str  # "approved" or "rejected"
    reviewed_by: str
