from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.core.security import hash_password
from app.db.session import get_db
from app.models import (
    Grade,
    Group,
    Project,
    Submission,
    TeamMemberRequest,
    TeamMemberRequestStatus,
    User,
    UserRole,
)
from app.repositories.repos import GroupRepository, UserRepository
from app.schemas import TeamMemberRequestApprove, TeamMemberRequestReject, UserCreate, UserUpdate
from app.schemas.schemas import normalize_display_id_for_role

router = APIRouter(prefix="/admin", tags=["Admin"])


def _user_to_dict(user: User, db: Session) -> dict:
    project_id = None
    if user.group_id:
        proj = db.scalar(select(Project).where(Project.group_id == user.group_id))
        if proj:
            project_id = proj.id
    return {
        "user_id": user.id,
        "display_id": user.display_id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "major": user.major,
        "group_id": user.group_id,
        "project_id": project_id,
        "must_change_password": user.must_change_password,
        "is_group_leader": user.is_group_leader,
        "created_at": user.created_at,
    }


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    return {
        "total_projects": db.scalar(select(func.count(Project.id))) or 0,
        "active_projects": db.scalar(
            select(func.count(Project.id)).where(Project.status == "Active")
        )
        or 0,
        "completed_projects": db.scalar(
            select(func.count(Project.id)).where(Project.status == "Completed")
        )
        or 0,
        "pending_projects": db.scalar(
            select(func.count(Project.id)).where(Project.status == "Pending")
        )
        or 0,
        "total_students": db.scalar(
            select(func.count(User.id)).where(User.role == "Student")
        )
        or 0,
        "total_supervisors": db.scalar(
            select(func.count(User.id)).where(User.role == "Supervisor")
        )
        or 0,
        "total_submissions": db.scalar(select(func.count(Submission.id))) or 0,
        "pending_grades": db.scalar(
            select(func.count(Grade.id)).where(Grade.approved.is_(None))
        )
        or 0,
        "total_groups": db.scalar(select(func.count(Group.id))) or 0,
    }


@router.get("/users")
def list_users(
    role: str | None = Query(None),
    major: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    if role == "Admin":
        role = "Coordinator"

    repo = UserRepository(db)
    users = repo.list_all(role=role, major=major, search=search)
    return [_user_to_dict(u, db) for u in users]


@router.post("/users", status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    repo = UserRepository(db)
    if repo.get_by_email(body.email):
        raise HTTPException(status_code=409, detail="البريد الإلكتروني مستخدم بالفعل")
    if repo.get_by_display_id(body.display_id):
        raise HTTPException(status_code=409, detail="المعرّف الظاهر مستخدم بالفعل")

    plain = body.password.strip() if body.password else "123456"
    user = repo.create(
        display_id=body.display_id,
        full_name=body.full_name,
        email=body.email,
        password_hash=hash_password(plain),
        role=body.role,
        major=body.major,
        must_change_password=True,
        is_group_leader=body.is_group_leader if body.role == "Student" else False,
    )
    db.commit()
    db.refresh(user)
    return _user_to_dict(user, db)


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    updates = body.model_dump(exclude_unset=True)
    new_role = updates.get("role", user.role)

    merged_major = user.major
    if "major" in updates:
        merged_major = updates["major"]

    if new_role == "Student" and merged_major is None:
        raise HTTPException(status_code=400, detail="يجب تحديد تخصص الطالب")

    disp = updates["display_id"] if "display_id" in updates else user.display_id
    try:
        normalized_display = normalize_display_id_for_role(
            new_role, disp, allow_legacy=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if "display_id" in updates or normalized_display != user.display_id:
        other = repo.get_by_display_id(normalized_display)
        if other is not None and other.id != user.id:
            raise HTTPException(status_code=409, detail="المعرّف الظاهر مستخدم بالفعل")

    updates["display_id"] = normalized_display

    if updates:
        repo.update(user, **updates)

    db.commit()
    db.refresh(user)
    return _user_to_dict(user, db)


def _member_request_dict(db: Session, req: TeamMemberRequest) -> dict:
    group = db.get(Group, req.group_id)
    requester = db.get(User, req.requested_by_id)
    approved = db.get(User, req.approved_user_id) if req.approved_user_id else None
    return {
        "id": req.id,
        "group_id": req.group_id,
        "group_name": group.name if group else None,
        "team_major": group.major if group else None,
        "requested_by_id": req.requested_by_id,
        "requested_by_name": requester.full_name if requester else None,
        "leader_display_id": requester.display_id if requester else None,
        "full_name": req.full_name,
        "email": req.email,
        "status": req.status,
        "coordinator_note": req.coordinator_note,
        "approved_user_id": req.approved_user_id,
        "approved_display_id": approved.display_id if approved else None,
        "created_at": req.created_at,
    }


@router.get("/member-requests")
def list_member_requests(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    stmt = select(TeamMemberRequest).order_by(TeamMemberRequest.created_at.desc())
    if status_filter:
        stmt = stmt.where(TeamMemberRequest.status == status_filter)
    rows = db.scalars(stmt).all()
    return [_member_request_dict(db, r) for r in rows]


@router.post("/member-requests/{request_id}/approve")
def approve_member_request(
    request_id: int,
    body: TeamMemberRequestApprove,
    db: Session = Depends(get_db),
    coordinator: User = Depends(require_role("Coordinator")),
):
    req = db.get(TeamMemberRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    if req.status != TeamMemberRequestStatus.pending.value:
        raise HTTPException(status_code=400, detail="تمت معالجة هذا الطلب مسبقاً")

    grp_repo = GroupRepository(db)
    user_repo = UserRepository(db)
    group = grp_repo.get_by_id(req.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="الفريق غير موجود")

    if grp_repo.member_count(group.id) >= 5:
        raise HTTPException(status_code=400, detail="الفريق مكتمل (5 أعضاء)")

    try:
        display_id = normalize_display_id_for_role("Student", body.display_id.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if user_repo.get_by_display_id(display_id):
        raise HTTPException(status_code=409, detail="المعرّف مستخدم بالفعل")
    if user_repo.get_by_email(req.email):
        raise HTTPException(status_code=409, detail="البريد مستخدم بالفعل")

    plain = (body.password or "123456").strip()
    student = user_repo.create(
        display_id=display_id,
        full_name=req.full_name,
        email=req.email,
        password_hash=hash_password(plain),
        role=UserRole.student.value,
        major=group.major,
        must_change_password=True,
        is_group_leader=False,
    )
    student.group_id = group.id

    req.status = TeamMemberRequestStatus.approved.value
    req.approved_user_id = student.id
    req.reviewed_by_id = coordinator.id
    req.reviewed_at = datetime.now(timezone.utc)
    req.coordinator_note = f"تم إنشاء الحساب بالمعرّف {display_id}"

    db.commit()
    db.refresh(student)
    return {
        "message": "تم اعتماد العضو وإنشاء حسابه",
        "request": _member_request_dict(db, req),
        "user": _user_to_dict(student, db),
    }


@router.post("/member-requests/{request_id}/reject")
def reject_member_request(
    request_id: int,
    body: TeamMemberRequestReject,
    db: Session = Depends(get_db),
    coordinator: User = Depends(require_role("Coordinator")),
):
    req = db.get(TeamMemberRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    if req.status != TeamMemberRequestStatus.pending.value:
        raise HTTPException(status_code=400, detail="تمت معالجة هذا الطلب مسبقاً")

    req.status = TeamMemberRequestStatus.rejected.value
    req.reviewed_by_id = coordinator.id
    req.reviewed_at = datetime.now(timezone.utc)
    req.coordinator_note = body.note
    db.commit()
    return {"message": "تم رفض الطلب", "request": _member_request_dict(db, req)}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    repo.delete(user)
    db.commit()
    return {"message": "تم حذف المستخدم بنجاح"}
