"""Group management — same-major constraint, max-5 members, no double-enrolment."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import UserRole
from app.repositories.repos import GroupRepository, UserRepository


def create_group(db: Session, *, name: str, member_ids: list[int], creator_id: int):
    user_repo = UserRepository(db)
    creator = user_repo.get_by_id(creator_id)
    if not creator or creator.role != UserRole.student.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "يمكن للطلاب فقط إنشاء المجموعات")

    if creator_id not in member_ids:
        member_ids = [creator_id, *member_ids]
    if len(member_ids) > 5:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "الحد الأقصى لعدد أعضاء المجموعة هو 5")

    members = []
    for uid in member_ids:
        u = user_repo.get_by_id(uid)
        if not u:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"المستخدم برقم {uid} غير موجود")
        if u.role != UserRole.student.value:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"المستخدم {u.full_name} ليس طالباً")
        members.append(u)

    majors = {m.major for m in members}
    if len(majors) != 1 or None in majors:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "يجب أن يكون جميع الأعضاء من نفس التخصص")
    shared_major = majors.pop()

    for m in members:
        if m.group_id is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, f"الطالب {m.full_name} منضم بالفعل لمجموعة أخرى")

    group_repo = GroupRepository(db)
    group = group_repo.create(name=name, major=shared_major, created_by=creator_id)
    for m in members:
        m.group_id = group.id

    db.commit()
    db.refresh(group)
    return group


def add_member(db: Session, *, group_id: int, user_id: int, requester_id: int):
    group_repo = GroupRepository(db)
    user_repo = UserRepository(db)

    group = group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(404, "المجموعة غير موجودة")

    requester = user_repo.get_by_id(requester_id)
    if not requester:
        raise HTTPException(404, "المستخدم غير موجود")
    if requester.role != UserRole.coordinator.value and requester.group_id != group_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ليس لديك صلاحية لإضافة أعضاء لهذه المجموعة")

    if group_repo.member_count(group_id) >= 5:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "المجموعة وصلت للحد الأقصى (5 أعضاء)")

    new_member = user_repo.get_by_id(user_id)
    if not new_member:
        raise HTTPException(404, "الطالب غير موجود")
    if new_member.role != UserRole.student.value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "يمكن إضافة الطلاب فقط للمجموعات")
    if new_member.group_id is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "الطالب منضم بالفعل لمجموعة أخرى")
    if new_member.major != group.major:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"تخصص الطالب ({new_member.major}) لا يتطابق مع تخصص المجموعة ({group.major})")

    new_member.group_id = group.id
    db.commit()
    db.refresh(group)
    return group


def remove_member(db: Session, *, group_id: int, user_id: int, requester_id: int):
    group_repo = GroupRepository(db)
    user_repo = UserRepository(db)

    group = group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(404, "المجموعة غير موجودة")

    requester = user_repo.get_by_id(requester_id)
    if not requester:
        raise HTTPException(404, "المستخدم غير موجود")
    if requester.role != UserRole.coordinator.value and requester_id != user_id and group.created_by != requester_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ليس لديك صلاحية لإزالة هذا العضو")

    member = user_repo.get_by_id(user_id)
    if not member or member.group_id != group_id:
        raise HTTPException(404, "العضو غير موجود في هذه المجموعة")

    member.group_id = None
    db.commit()


def get_group_detail(db: Session, group_id: int) -> dict:
    group_repo = GroupRepository(db)
    group = group_repo.get_by_id(group_id)
    if not group:
        raise HTTPException(404, "المجموعة غير موجودة")

    members = group_repo.get_members(group_id)
    members_list = [
        {"id": m.id, "display_id": m.display_id, "full_name": m.full_name, "email": m.email, "major": m.major}
        for m in members
    ]
    project_info = None
    if group.project:
        project_info = {"id": group.project.id, "title": group.project.title, "status": group.project.status}

    return {
        "id": group.id, "name": group.name, "major": group.major,
        "created_by": group.created_by, "created_at": group.created_at,
        "members": members_list, "member_count": len(members_list), "project": project_info,
    }
