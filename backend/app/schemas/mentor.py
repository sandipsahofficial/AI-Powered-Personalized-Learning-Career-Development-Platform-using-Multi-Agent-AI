import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ChatMessageItem(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MentorChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class MentorChatResponse(BaseModel):
    reply: str
    timestamp: datetime
    active_role: Optional[str] = None
    readiness_percentage: Optional[float] = None
    current_milestone: Optional[str] = None


class MentorConversationHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_title: str
    messages: List[Dict[str, Any]]
    last_interaction_at: datetime
