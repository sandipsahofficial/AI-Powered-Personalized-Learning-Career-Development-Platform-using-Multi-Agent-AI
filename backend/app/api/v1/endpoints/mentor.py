import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.mentor_service import MentorService
from app.schemas.mentor import (
    MentorChatRequest,
    MentorChatResponse,
    MentorConversationHistoryResponse
)

router = APIRouter()


@router.post("/chat", response_model=MentorChatResponse, summary="Chat with AI Career Mentor")
async def chat_with_mentor(
    request: MentorChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Interacts with the AI Career Mentor using the learner's actual profile, skills, goal, and milestone context."""
    return await MentorService.chat(current_user.id, request.message, db)


@router.get("/history", response_model=Optional[MentorConversationHistoryResponse], summary="Get Mentorship Conversation History")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves previous chat messages with the AI Career Mentor."""
    return await MentorService.get_conversation_history(current_user.id, db)
