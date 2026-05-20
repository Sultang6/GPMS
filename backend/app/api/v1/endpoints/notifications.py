from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models import Notification, Project, User, UserRole
from app.repositories.repos import UserRepository
from app.schemas import NotificationCreate

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _notif_to_dict(n: Notification) -> dict:
    return {
        "notification_id": n.id,
        "user_id": n.user_id,
        "sender_id": n.sender_id,
        "title": n.title,
        "content": n.content,
        "is_read": n.is_read,
        "created_at": n.created_at,
    }


def _assert_can_notify(db: Session, sender: User, recipient_id: int) -> User:
    user_repo = UserRepository(db)
    recipient = user_repo.get_by_id(recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="المستلم غير موجود")

    if sender.role == UserRole.coordinator.value:
        return recipient

    if sender.role == UserRole.supervisor.value:
        if recipient.role != UserRole.student.value:
            raise HTTPException(status_code=403, detail="المشرف يرسل إشعارات للطلاب فقط")
        if not recipient.group_id:
            raise HTTPException(status_code=403, detail="الطالب غير مرتبط بمجموعة")
        supervised = db.scalar(
            select(Project.id).where(
                Project.supervisor_id == sender.id,
                Project.group_id == recipient.group_id,
            )
        )
        if not supervised:
            raise HTTPException(
                status_code=403,
                detail="لا يمكنك إرسال إشعار لطالب خارج مشاريعك",
            )
        return recipient

    raise HTTPException(status_code=403, detail="لا صلاحية لإرسال إشعارات")


@router.get("")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    notifs = list(db.scalars(stmt).all())
    return [_notif_to_dict(n) for n in notifs]


@router.post("", status_code=201)
def create_notification(
    body: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Supervisor", "Coordinator")),
):
    _assert_can_notify(db, current_user, body.user_id)
    notif = Notification(
        user_id=body.user_id,
        sender_id=current_user.id,
        title=body.title,
        content=body.content,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return _notif_to_dict(notif)


@router.patch("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return {"message": "تم تحديد جميع الإشعارات كمقروءة"}


@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.get(Notification, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="الإشعار غير موجود")
    if notif.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="لا يمكنك تعديل إشعار مستخدم آخر")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return _notif_to_dict(notif)
