from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas import ChatbotRequest, ChatbotResponse
from app.services.chatbot_service import process_message

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.post("/ask", response_model=ChatbotResponse)
def ask(
    body: ChatbotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lang = body.lang if body.lang in ("ar", "en") else "ar"
    result = process_message(db, current_user, body.message, lang)
    return ChatbotResponse(
        reply=result.reply,
        intent=result.intent,
        from_memory=result.from_memory,
        interaction_id=result.interaction_id,
    )
