"""
Pydantic models for API
"""
from pydantic import BaseModel
from typing import List, Optional


class Message(BaseModel):
    """Chat message model"""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_history: Optional[List[Message]] = []


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    status: str
    tools_used: Optional[List[str]] = []
    used_local_kb: Optional[bool] = False
    used_web_search: Optional[bool] = False
