"""Pydantic models for request/response validation."""

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ApprovalUpdate(BaseModel):
    status: str  # "approved" or "rejected"
    reviewed_by: str
