from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session



from app.core.deps import get_current_user, require_role

from app.db.session import get_db

from app.models import GradeCategory, Project, User

from app.repositories.repos import GradeRepository, ProjectRepository, UserRepository

from app.schemas import GradeBulkInput, GradeInput



router = APIRouter(prefix="/grades", tags=["Grades"])



LEGACY_CATEGORY_MAX = 25.0

EXTRA_CATEGORIES = frozenset({"group_report", "individual_contribution"})

VALID_CATEGORIES: set[str] = {c.value for c in GradeCategory} | EXTRA_CATEGORIES





def _grade_to_dict(g) -> dict:

    return {

        "id": g.id,

        "student_id": g.student_id,

        "project_id": g.project_id,

        "supervisor_id": g.supervisor_id,

        "category": g.category,

        "score": float(g.score),

        "max_score": float(g.max_score),

        "feedback": g.feedback,

        "approved": g.approved,

        "created_at": g.created_at,

    }





def _ensure_supervisor_or_coordinator_project(supervisor: User, project: Project) -> None:

    if supervisor.role == "Coordinator":

        return

    if supervisor.role == "Supervisor" and project.supervisor_id == supervisor.id:

        return

    raise HTTPException(

        status_code=status.HTTP_403_FORBIDDEN,

        detail="أنت لست المشرف أو المنسق المرتبط بهذا المشروع",

    )





def _category_max_score(project: Project, category: str) -> float:

    if category == "group_report":

        return float(project.grading_report_weight)

    if category == "individual_contribution":

        return float(project.grading_individual_weight)

    return LEGACY_CATEGORY_MAX





def _do_grade(

    db: Session,

    *,

    supervisor: User,

    student_id: int,

    project_id: int,

    category: str,

    score: float,

    feedback: str | None,

):

    proj_repo = ProjectRepository(db)

    project = proj_repo.get_by_id(project_id)

    if not project:

        raise HTTPException(status_code=404, detail="المشروع غير موجود")



    _ensure_supervisor_or_coordinator_project(supervisor, project)



    user_repo = UserRepository(db)

    student = user_repo.get_by_id(student_id)

    if not student:

        raise HTTPException(status_code=404, detail="الطالب غير موجود")

    if not project.group_id or student.group_id != project.group_id:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="الطالب ليس ضمن مجموعة هذا المشروع",

        )



    if category not in VALID_CATEGORIES:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail=f"الفئة غير صالحة. الفئات المتاحة: {', '.join(sorted(VALID_CATEGORIES))}",

        )



    mx = _category_max_score(project, category)

    if not 0 <= score <= mx:

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail=f"الدرجة يجب أن تكون بين 0 و {mx} لهذه الفئة",

        )



    grade_repo = GradeRepository(db)

    grade = grade_repo.upsert(

        student_id=student_id,

        project_id=project_id,

        supervisor_id=supervisor.id,

        category=category,

        score=score,

        max_score=mx,

        feedback=feedback,

    )

    return grade





@router.post("/individual", status_code=201)

def grade_individual(

    body: GradeInput,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("Supervisor", "Coordinator")),

):

    grade = _do_grade(

        db,

        supervisor=current_user,

        student_id=body.student_id,

        project_id=body.project_id,

        category=body.category,

        score=body.score,

        feedback=body.feedback,

    )

    db.commit()

    db.refresh(grade)

    return _grade_to_dict(grade)





@router.post("/bulk", status_code=201)

def grade_bulk(

    body: GradeBulkInput,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("Supervisor", "Coordinator")),

):

    results = []

    for cat in GradeCategory:

        score = getattr(body, cat.value)

        grade = _do_grade(

            db,

            supervisor=current_user,

            student_id=body.student_id,

            project_id=body.project_id,

            category=cat.value,

            score=score,

            feedback=body.feedback,

        )

        results.append(grade)



    db.commit()

    for g in results:

        db.refresh(g)

    return [_grade_to_dict(g) for g in results]





@router.get("/student/{student_id}/project/{project_id}")

def get_student_grades(

    student_id: int,

    project_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    user_repo = UserRepository(db)

    student = user_repo.get_by_id(student_id)

    if not student:

        raise HTTPException(status_code=404, detail="الطالب غير موجود")



    proj = db.get(Project, project_id)

    if not proj:

        raise HTTPException(status_code=404, detail="المشروع غير موجود")



    if current_user.role != "Coordinator":

        if current_user.role == "Student" and current_user.id != student_id:

            raise HTTPException(status_code=403, detail="لا يمكنك عرض درجات طالب آخر")

        if current_user.role == "Supervisor" and proj.supervisor_id != current_user.id:

            raise HTTPException(status_code=403, detail="لا يمكنك عرض درجات هذا المشروع")



    grade_repo = GradeRepository(db)

    grades = grade_repo.get_student_grades(student_id, project_id)



    total = sum(float(g.score) for g in grades)

    max_total = sum(float(g.max_score) for g in grades)

    all_approved = all(g.approved is True for g in grades) if grades else None



    return {

        "student_id": student_id,

        "display_id": student.display_id,

        "full_name": student.full_name,

        "project_id": project_id,

        "total_score": total,

        "max_total": max_total,

        "categories": [_grade_to_dict(g) for g in grades],

        "approved": all_approved,

    }





@router.patch("/{grade_id}/approve")

def approve_grade(

    grade_id: int,

    approved: bool = Query(...),

    db: Session = Depends(get_db),

    _current: User = Depends(require_role("Coordinator")),

):

    grade_repo = GradeRepository(db)

    try:

        grade = grade_repo.approve(grade_id, approved)

    except ValueError:

        raise HTTPException(status_code=404, detail="الدرجة غير موجودة")

    db.commit()

    db.refresh(grade)

    return _grade_to_dict(grade)





@router.get("/pending-approval")

def get_pending_approval(

    db: Session = Depends(get_db),

    _current: User = Depends(require_role("Coordinator")),

):

    grade_repo = GradeRepository(db)

    grades = grade_repo.list_pending_approval()

    return [_grade_to_dict(g) for g in grades]


