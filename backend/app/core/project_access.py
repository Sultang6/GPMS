"""Project & file access control — centralized authorization checks."""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FileRecord, Project, Submission, User, UserRole


def _student_in_project(user: User, project: Project) -> bool:
    return bool(user.group_id and project.group_id and user.group_id == project.group_id)


def assert_can_view_project(user: User, project: Project) -> None:
    if user.role == UserRole.coordinator.value:
        return
    if user.role == UserRole.supervisor.value and project.supervisor_id == user.id:
        return
    if user.role == UserRole.student.value and _student_in_project(user, project):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="لا صلاحية لك لعرض هذا المشروع",
    )


def assert_can_edit_project(user: User, project: Project) -> None:
    if user.role == UserRole.coordinator.value:
        return
    if user.role == UserRole.supervisor.value and project.supervisor_id == user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="لا صلاحية لك لتعديل هذا المشروع",
    )


def assert_can_manage_project(user: User, project: Project) -> None:
    """Coordinator or assigned supervisor — grading / reports."""
    if user.role == UserRole.coordinator.value:
        return
    if user.role == UserRole.supervisor.value and project.supervisor_id == user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="لا صلاحية لك لإدارة هذا المشروع",
    )


def member_dict(user: User, viewer: User) -> dict:
    """Student roster entry — hide email unless coordinator/supervisor."""
    data = {
        "user_id": user.id,
        "display_id": user.display_id,
        "full_name": user.full_name,
        "role": user.role,
        "major": user.major,
        "group_id": user.group_id,
        "created_at": user.created_at,
    }
    if viewer.role in (UserRole.coordinator.value, UserRole.supervisor.value):
        data["email"] = user.email
    elif viewer.role == UserRole.student.value and viewer.group_id == user.group_id:
        data["email"] = user.email
    return data


def assert_can_download_file(db: Session, user: User, record: FileRecord) -> None:
    if user.role == UserRole.coordinator.value:
        return
    if record.uploader_id == user.id:
        return

    sub = db.scalar(select(Submission).where(Submission.file_id == record.id))
    if sub is None:
        raise HTTPException(status_code=403, detail="لا صلاحية لتحميل هذا الملف")

    project = db.get(Project, sub.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")

    if user.role == UserRole.supervisor.value and project.supervisor_id == user.id:
        return

    if user.role == UserRole.student.value:
        if sub.student_id == user.id:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="لا صلاحية لتحميل هذا الملف",
    )
