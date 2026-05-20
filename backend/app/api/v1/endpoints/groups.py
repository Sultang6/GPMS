from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Group, TeamMemberRequest, TeamMemberRequestStatus, User, UserRole
from app.repositories.repos import GroupRepository, UserRepository
from app.schemas import (
    GroupAddMember,
    GroupAddMemberByDisplayId,
    GroupCreate,
    TeamMemberRequestCreate,
)

router = APIRouter(prefix="/groups", tags=["Groups"])


def _group_summary(group, repo: GroupRepository) -> dict:
    return {
        "id": group.id,
        "name": group.name,
        "major": group.major,
        "created_by": group.created_by,
        "created_at": group.created_at,
        "member_count": repo.member_count(group.id),
    }


def _pending_request_count(db: Session, group_id: int) -> int:
    return (
        db.scalar(
            select(func.count(TeamMemberRequest.id)).where(
                TeamMemberRequest.group_id == group_id,
                TeamMemberRequest.status == TeamMemberRequestStatus.pending.value,
            )
        )
        or 0
    )


def _request_row(db: Session, req: TeamMemberRequest) -> dict:
    approved = db.get(User, req.approved_user_id) if req.approved_user_id else None
    requester = db.get(User, req.requested_by_id)
    group = db.get(Group, req.group_id)
    return {
        "id": req.id,
        "group_id": req.group_id,
        "group_name": group.name if group else None,
        "team_major": group.major if group else None,
        "requested_by_id": req.requested_by_id,
        "requested_by_name": requester.full_name if requester else None,
        "full_name": req.full_name,
        "email": req.email,
        "status": req.status,
        "coordinator_note": req.coordinator_note,
        "approved_user_id": req.approved_user_id,
        "approved_display_id": approved.display_id if approved else None,
        "created_at": req.created_at,
    }


def _assert_leader_can_add_slot(db: Session, group_id: int, grp_repo: GroupRepository) -> None:
    members = grp_repo.member_count(group_id)
    pending = _pending_request_count(db, group_id)
    if members + pending >= 5:
        raise HTTPException(
            status_code=400,
            detail="الحد الأقصى للفريق خمسة طلاب (بما فيهم الطلبات بانتظار موافقة المنسق)",
        )


def _group_detail(group, grp_repo: GroupRepository, db: Session) -> dict:
    members_list = [
        {
            "user_id": m.id,
            "display_id": m.display_id,
            "full_name": m.full_name,
            "email": m.email,
            "role": m.role,
            "major": m.major,
            "group_id": m.group_id,
            "is_leader": m.id == group.created_by,
            "created_at": m.created_at,
        }
        for m in grp_repo.get_members(group.id)
    ]
    project_info = None
    if group.project:
        project_info = {
            "id": group.project.id,
            "title": group.project.title,
            "status": group.project.status,
            "supervisor_id": group.project.supervisor_id,
        }
    leader = next((m for m in grp_repo.get_members(group.id) if m.id == group.created_by), None)
    requests = db.scalars(
        select(TeamMemberRequest)
        .where(TeamMemberRequest.group_id == group.id)
        .order_by(TeamMemberRequest.created_at.desc())
    ).all()
    return {
        "id": group.id,
        "name": group.name,
        "major": group.major,
        "created_by": group.created_by,
        "leader_name": leader.full_name if leader else None,
        "leader_display_id": leader.display_id if leader else None,
        "created_at": group.created_at,
        "members": members_list,
        "member_count": len(members_list),
        "member_requests": [_request_row(db, r) for r in requests],
        "pending_request_count": sum(
            1 for r in requests if r.status == TeamMemberRequestStatus.pending.value
        ),
        "project": project_info,
    }


@router.post("", status_code=201)
def create_group(
    body: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.student.value:
        raise HTTPException(status_code=403, detail="يمكن للطلاب فقط إنشاء المجموعات")

    if current_user.group_id is not None:
        raise HTTPException(status_code=403, detail="أنت منضم لفريق بالفعل.")

    if not current_user.is_group_leader:
        raise HTTPException(status_code=403, detail="تكوين الفريق متاح لقائد الفريق فقط")

    if current_user.major is None:
        raise HTTPException(status_code=400, detail="تخصصك غير محدد. تواصل مع المنسق.")

    if body.member_ids or body.member_display_ids:
        pass  # يُتجاهل — الأعضاء يُضافون عبر طلبات للمنسق

    grp_repo = GroupRepository(db)
    group = grp_repo.create(
        name=body.name,
        major=current_user.major,
        created_by=current_user.id,
    )
    current_user.group_id = group.id
    db.commit()
    db.refresh(group)
    return _group_summary(group, grp_repo)


@router.get("")
def list_groups(
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    repo = GroupRepository(db)
    return [_group_summary(g, repo) for g in repo.list_all()]


@router.get("/teams-overview")
def teams_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (
        UserRole.coordinator.value,
        UserRole.supervisor.value,
    ):
        raise HTTPException(status_code=403, detail="غير مصرح")

    grp_repo = GroupRepository(db)
    out: list[dict] = []
    for group in grp_repo.list_all():
        if current_user.role == UserRole.supervisor.value:
            if not group.project or group.project.supervisor_id != current_user.id:
                continue
        out.append(_group_detail(group, grp_repo, db))
    return out


@router.get("/mine")
def my_group(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.group_id:
        raise HTTPException(status_code=404, detail="لست منضماً لفريق بعد")
    grp_repo = GroupRepository(db)
    group = grp_repo.get_by_id(current_user.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="المجموعة غير موجودة")
    return _group_detail(group, grp_repo, db)


@router.post("/mine/member-requests", status_code=201)
def submit_member_request(
    body: TeamMemberRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.group_id:
        raise HTTPException(status_code=400, detail="يجب تكوين الفريق أولاً")

    grp_repo = GroupRepository(db)
    group = grp_repo.get_by_id(current_user.group_id)
    if not group or group.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="إرسال طلبات الأعضاء متاح لقائد الفريق فقط")

    email = body.email.strip().lower()
    user_repo = UserRepository(db)
    if user_repo.get_by_email(email):
        raise HTTPException(status_code=409, detail="البريد الإلكتروني مسجّل مسبقاً في النظام")

    dup = db.scalar(
        select(TeamMemberRequest).where(
            TeamMemberRequest.group_id == group.id,
            TeamMemberRequest.email == email,
            TeamMemberRequest.status == TeamMemberRequestStatus.pending.value,
        )
    )
    if dup:
        raise HTTPException(status_code=409, detail="يوجد طلب معلّق بنفس البريد")

    _assert_leader_can_add_slot(db, group.id, grp_repo)

    req = TeamMemberRequest(
        group_id=group.id,
        requested_by_id=current_user.id,
        full_name=body.full_name.strip(),
        email=email,
        status=TeamMemberRequestStatus.pending.value,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _request_row(db, req)


@router.delete("/mine/member-requests/{request_id}")
def cancel_member_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = db.get(TeamMemberRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    if req.requested_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="لا يمكنك إلغاء هذا الطلب")
    if req.status != TeamMemberRequestStatus.pending.value:
        raise HTTPException(status_code=400, detail="لا يمكن إلغاء طلب تمت معالجته")
    db.delete(req)
    db.commit()
    return {"message": "تم إلغاء الطلب"}


def _attach_member_to_group(
    db: Session,
    *,
    group,
    new_member: User,
    grp_repo: GroupRepository,
) -> None:
    if grp_repo.member_count(group.id) >= 5:
        raise HTTPException(status_code=400, detail="المجموعة وصلت للحد الأقصى (5 أعضاء)")
    if new_member.role != UserRole.student.value:
        raise HTTPException(status_code=400, detail="يمكن إضافة الطلاب فقط")
    if new_member.is_group_leader:
        raise HTTPException(status_code=400, detail="لا يمكن إضافة حساب قائد فريق كعضو")
    if new_member.group_id is not None:
        raise HTTPException(status_code=409, detail="الطالب منضم لفريق آخر")
    if new_member.major != group.major:
        raise HTTPException(status_code=400, detail="يجب أن يكون العضو بنفس تخصص الفريق")
    new_member.group_id = group.id


@router.get("/{group_id}")
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    grp_repo = GroupRepository(db)
    group = grp_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="المجموعة غير موجودة")
    return _group_detail(group, grp_repo, db)


@router.post("/{group_id}/members")
def add_member(
    group_id: int,
    body: GroupAddMember,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.coordinator.value:
        raise HTTPException(status_code=403, detail="إضافة الأعضاء مباشرة متاحة للمنسق فقط")

    grp_repo = GroupRepository(db)
    user_repo = UserRepository(db)
    group = grp_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="المجموعة غير موجودة")

    new_member = user_repo.get_by_id(body.user_id)
    if not new_member:
        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    _attach_member_to_group(db, group=group, new_member=new_member, grp_repo=grp_repo)
    db.commit()
    db.refresh(group)
    return _group_detail(group, grp_repo, db)


@router.post("/{group_id}/members/by-display-id", status_code=201)
def add_member_by_display_id(
    group_id: int,
    body: GroupAddMemberByDisplayId,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.student.value:
        raise HTTPException(
            status_code=403,
            detail=(
                "لا يمكن إضافة عضو بالمعرّف مباشرة. أرسل طلباً باسم العضو وبريده "
                "ليعتمدها المنسق ويُنشئ الحساب."
            ),
        )

    grp_repo = GroupRepository(db)
    user_repo = UserRepository(db)
    group = grp_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="المجموعة غير موجودة")

    did = body.display_id.strip()
    new_member = user_repo.get_by_display_id(did)
    if not new_member:
        raise HTTPException(status_code=404, detail="لم يتم العثور على المعرّف")

    _attach_member_to_group(db, group=group, new_member=new_member, grp_repo=grp_repo)
    db.commit()
    db.refresh(group)
    return _group_detail(group, grp_repo, db)


@router.delete("/{group_id}/members/{user_id}")
def remove_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    grp_repo = GroupRepository(db)
    user_repo = UserRepository(db)

    group = grp_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="المجموعة غير موجودة")

    is_coordinator = current_user.role == UserRole.coordinator.value
    is_creator = group.created_by == current_user.id
    if not is_coordinator and not is_creator:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية لإزالة هذا العضو")

    if user_id == group.created_by:
        raise HTTPException(status_code=400, detail="لا يمكن إزالة قائد الفريق")

    member = user_repo.get_by_id(user_id)
    if not member or member.group_id != group_id:
        raise HTTPException(status_code=404, detail="العضو غير موجود في هذه المجموعة")

    member.group_id = None
    db.commit()
    return {"message": "تم إزالة العضو بنجاح"}
