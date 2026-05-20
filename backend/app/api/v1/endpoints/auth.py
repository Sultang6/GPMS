from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_current_user_optional, require_role
from app.core.rate_limit import check_rate_limit
from app.core.team_access import student_team_context
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Project, User, UserRole
from app.repositories.repos import ProjectRepository, UserRepository
from app.schemas import ChangePasswordRequest, LoginRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

_REDIRECT = {
    "Student": "/pages/student/student_dashboard.html",
    "Supervisor": "/pages/supervisor/supervisor_dashboard.html",
    "Coordinator": "/pages/admin/admin_dashboard.html",
}


@router.post("/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, key_prefix="login", max_attempts=15, window_seconds=60)
    repo = UserRepository(db)
    user: User | None = None

    if body.user_id is not None:
        user = repo.get_by_id(body.user_id)
    elif body.display_id:
        user = repo.get_by_display_id(body.display_id)
    elif body.email:
        user = repo.get_by_email(body.email)

    if not user:
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")

    role = body.role
    if role == "Admin":
        role = "Coordinator"
    if role and user.role != role:
        raise HTTPException(status_code=403, detail="الدور المحدد لا يتطابق مع حسابك")

    token = create_access_token(subject=user.id)
    team = student_team_context(db, user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "display_id": user.display_id,
        "full_name": user.full_name,
        "role": user.role,
        "redirect_url": _REDIRECT.get(user.role, "/GPMS.html"),
        "must_change_password": bool(user.must_change_password),
        "is_team_leader": team["is_team_leader"],
        "is_team_member": team["is_team_member"],
        "is_group_leader_account": bool(user.is_group_leader),
        "team_name": team["team_name"],
        "team_members": team["team_members"],
    }


@router.get("/me")
def read_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ملف الطالب الحالي — للتحقق من المجموعة والمشروع قبل تسجيل فريق جديد."""
    project_id = None
    if current_user.group_id:
        proj = db.scalar(select(Project).where(Project.group_id == current_user.group_id))
        if proj:
            project_id = proj.id
    team = student_team_context(db, current_user)
    return {
        "user_id": current_user.id,
        "display_id": current_user.display_id,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "major": current_user.major,
        "group_id": current_user.group_id,
        "project_id": project_id,
        "must_change_password": bool(current_user.must_change_password),
        "is_team_leader": team["is_team_leader"],
        "is_team_member": team["is_team_member"],
        "is_group_leader_account": bool(current_user.is_group_leader),
        "team_name": team["team_name"],
        "team_members": team["team_members"],
    }


@router.get("/teammate-preview")
def teammate_preview(
    display_id: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """البحث عن زميل بالمعرّف الظاهر — لقائد الفريق فقط (حسابات أعضاء سجّلها المنسق)."""
    if current_user.role != UserRole.student.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذه الخدمة مخصصة للطلاب",
        )

    leader_ctx = student_team_context(db, current_user)
    if not leader_ctx["is_team_leader"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="إضافة أعضاء الفريق متاحة لقائد الفريق فقط",
        )

    if current_user.major is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="تعذر تكوين فريق: تخصصك غير محدد في النظام. تواصل مع المنسق.",
        )

    repo = UserRepository(db)
    did = display_id.strip()
    candidate = repo.get_by_display_id(did)
    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=(
                "لم يتم العثور على هذا المعرّف. يجب أن يسجّل المنسق حساب الطالب "
                "(عضو فريق، وليس قائد) بنفس التخصص قبل إضافته."
            ),
        )

    if candidate.role != UserRole.student.value:
        raise HTTPException(status_code=400, detail="المعرّف لا يخص حساب طالب")

    if candidate.is_group_leader:
        raise HTTPException(
            status_code=400,
            detail="هذا المعرّف لحساب قائد فريق. أضف فقط معرّفات أعضاء الفريق.",
        )

    if candidate.id == current_user.id:
        raise HTTPException(status_code=400, detail="أنت مسجّل كقائد الفريق؛ لا حاجة لإضافة نفسك")

    if candidate.major is None or candidate.major != current_user.major:
        raise HTTPException(
            status_code=400,
            detail="جميع أعضاء الفريق يجب أن يكونوا بنفس التخصص المعرّف في حسابكم",
        )

    if candidate.group_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="هذا الطالب منضم إلى مجموعة أخرى بالفعل",
        )

    return {
        "user_id": candidate.id,
        "display_id": candidate.display_id,
        "full_name": candidate.full_name,
        "major": candidate.major,
    }


@router.get("/supervisors")
def list_supervisors_for_dropdown(
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    """قائمة المشرفين لاختيار المشرف المقترح — أي مستخدم مسجّل الدخول."""
    repo = UserRepository(db)
    sups = repo.list_all(role="Supervisor")
    return [
        {"user_id": u.id, "display_id": u.display_id, "full_name": u.full_name}
        for u in sups
    ]


@router.patch("/change-password")
def change_password_first_login(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="كلمة المرور الحالية غير صحيحة")

    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="يجب أن تكون كلمة المرور الجديدة مختلفة عن الحالية",
        )

    current_user.password_hash = hash_password(body.new_password)
    current_user.must_change_password = False
    db.commit()
    db.refresh(current_user)

    token = create_access_token(subject=current_user.id)
    return {
        "message": "تم تحديث كلمة المرور",
        "access_token": token,
        "must_change_password": False,
    }


@router.post("/seed-demo-users")
def seed_demo_users(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if settings.is_production:
        raise HTTPException(status_code=403, detail="تعطيل في بيئة الإنتاج")

    user_repo = UserRepository(db)
    if user_repo.count() > 0:
        if current_user is None or current_user.role != UserRole.coordinator.value:
            raise HTTPException(
                status_code=403,
                detail="يتطلب حساب منسق لتشغيل البذور عند وجود مستخدمين",
            )
    elif not settings.seed_allow_unauthenticated:
        raise HTTPException(status_code=403, detail="البذور الأولية معطّلة")

    return auth_service.seed_demo_users(db)


@router.patch("/assign-project")
def assign_project(
    user_id: int = Query(...),
    project_id: int = Query(...),
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    user_repo = UserRepository(db)
    proj_repo = ProjectRepository(db)

    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    project = proj_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")

    if project.group_id is None:
        raise HTTPException(
            status_code=400,
            detail="المشروع ليس مرتبطاً بمجموعة بعد",
        )

    user.group_id = project.group_id
    db.commit()
    db.refresh(user)
    return {
        "message": "تم ربط المستخدم بالمشروع بنجاح",
        "user_id": user.id,
        "project_id": project.id,
    }
