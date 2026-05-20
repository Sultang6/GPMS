"""صلاحيات قائد الفريق مقابل عضو الفريق (بدون دور مستخدم جديد)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Group, User, UserRole


def student_team_context(db: Session, user: User) -> dict:
    """
    - طالب بلا مجموعة: يُعامل كقائد (يمكنه تسجيل فريق ومشروع).
    - طالب في مجموعة و``created_by`` = معرفه: قائد الفريق.
    - طالب في مجموعة وليس القائد: عضو فريق (صلاحيات محدودة).
    """
    empty = {
        "is_team_leader": False,
        "is_team_member": False,
        "team_name": None,
        "team_members": [],
    }
    if user.role != UserRole.student.value:
        return empty

    if not user.group_id:
        return {
            "is_team_leader": bool(user.is_group_leader),
            "is_team_member": False,
            "team_name": None,
            "team_members": [],
        }

    group = db.get(Group, user.group_id)
    if not group:
        return empty

    is_leader = group.created_by == user.id
    members = list(
        db.scalars(select(User).where(User.group_id == group.id).order_by(User.id)).all()
    )
    team_members = [
        {
            "user_id": m.id,
            "display_id": m.display_id,
            "full_name": m.full_name,
            "is_leader": m.id == group.created_by,
        }
        for m in members
    ]
    return {
        "is_team_leader": is_leader,
        "is_team_member": not is_leader,
        "team_name": group.name,
        "team_members": team_members,
    }


def assert_team_leader(db: Session, user: User) -> None:
    """يرفع 403 إذا كان الطالب عضو فريق وليس القائد."""
    from fastapi import HTTPException, status

    ctx = student_team_context(db, user)
    if user.role == UserRole.student.value and ctx["is_team_member"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذا الإجراء متاح لقائد الفريق فقط (تسجيل المشروع ورفع التقارير)",
        )
