"""Authentication & demo-data seeding."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import Major, ProjectStatus, UserRole
from app.repositories.repos import GroupRepository, ProjectRepository, UserRepository


def login(
    db: Session,
    *,
    user_id: int | None = None,
    display_id: str | None = None,
    email: str | None = None,
    password: str,
    role: str | None = None,
):
    repo = UserRepository(db)
    user = None

    if user_id is not None:
        user = repo.get_by_id(user_id)
    elif display_id:
        user = repo.get_by_display_id(display_id)
    elif email:
        user = repo.get_by_email(email)

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "بيانات الدخول غير صحيحة")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "كلمة المرور غير صحيحة")

    if role and user.role != role:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "الدور المحدد لا يتطابق مع حسابك")

    return user


def seed_demo_users(db: Session) -> dict:
    user_repo = UserRepository(db)
    if user_repo.count() > 0:
        return {"message": "يوجد مستخدمون بالفعل، لم يتم إنشاء بيانات تجريبية"}

    pw = hash_password("123456")

    coordinator = user_repo.create(
        display_id="90001",
        full_name="منسق القسم",
        email="coordinator@gpms.local",
        password_hash=pw,
        role=UserRole.coordinator.value,
        must_change_password=False,
        is_group_leader=False,
    )
    sup1 = user_repo.create(
        display_id="91001",
        full_name="د. أحمد المشرف",
        email="supervisor1@gpms.local",
        password_hash=pw,
        role=UserRole.supervisor.value,
        must_change_password=False,
    )
    sup2 = user_repo.create(
        display_id="91002",
        full_name="د. فاطمة المشرفة",
        email="supervisor2@gpms.local",
        password_hash=pw,
        role=UserRole.supervisor.value,
        must_change_password=False,
    )

    students = []
    for i, (did, name, em) in enumerate([
        ("2584", "خالد الطالب", "student1@gpms.local"),
        ("2585", "سارة الطالبة", "student2@gpms.local"),
        ("2586", "محمد الطالب", "student3@gpms.local"),
        ("2587", "نورة الطالبة", "student4@gpms.local"),
    ]):
        s = user_repo.create(
            display_id=did,
            full_name=name,
            email=em,
            password_hash=pw,
            role=UserRole.student.value,
            major=Major.cs.value,
            must_change_password=False,
            is_group_leader=(i == 0),
        )
        students.append(s)

    group_repo = GroupRepository(db)
    group = group_repo.create(name="فريق GPMS", major=Major.cs.value, created_by=students[0].id)
    for s in students:
        s.group_id = group.id

    proj_repo = ProjectRepository(db)
    project = proj_repo.create(
        title="نظام إدارة مشاريع التخرج",
        description="نظام متكامل لإدارة ومتابعة مشاريع التخرج في قسم علوم الحاسب",
        status=ProjectStatus.active.value,
        group_id=group.id,
        supervisor_id=sup1.id,
    )

    db.commit()
    return {
        "message": "تم إنشاء البيانات التجريبية بنجاح",
        "password": "123456",
        "login_hint": "تسجيل الدخول باستخدام المعرف المكون من 4 أو 5 أرقام (حسب الدور)، وكلمة المرور أعلاه",
        "coordinator": coordinator.display_id,
        "supervisors": [sup1.display_id, sup2.display_id],
        "students": [s.display_id for s in students],
        "group": group.name,
        "project": project.title,
    }
