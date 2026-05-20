from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Message, Project, User
from app.schemas import MessageCreate

router = APIRouter(prefix="/messages", tags=["Messages"])


def _message_to_dict(m: Message) -> dict:
    return {
        "message_id": m.id,
        "sender_id": m.sender_id,
        "project_id": m.project_id,
        "content": m.content,
        "sent_at": m.sent_at,
    }


@router.get("")
def list_messages(
    project_id: int = Query(...),
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    stmt = (
        select(Message)
        .where(Message.project_id == project_id)
        .order_by(Message.sent_at.asc())
    )
    msgs = list(db.scalars(stmt).all())
    return [_message_to_dict(m) for m in msgs]


@router.post("", status_code=201)
def create_message(
    body: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    proj = db.get(Project, body.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")

    msg = Message(
        sender_id=current_user.id,
        project_id=body.project_id,
        content=body.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return _message_to_dict(msg)
