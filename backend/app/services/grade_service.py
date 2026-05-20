"""Individual grading — 4 categories × 25 pts = 100 total."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import GradeCategory, UserRole
from app.repositories.repos import GradeRepository, ProjectRepository, UserRepository

VALID_CATEGORIES: set[str] = {c.value for c in GradeCategory}


def grade_student(
    db: Session, *, supervisor_id: int, student_id: int,
    project_id: int, category: str, score: float, feedback: str | None = None,
):
    proj_repo = ProjectRepository(db)
    user_repo = UserRepository(db)
    grade_repo = GradeRepository(db)

    project = proj_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(404, "المشروع غير موجود")
    if project.supervisor_id != supervisor_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "أنت لست المشرف على هذا المشروع")

    student = user_repo.get_by_id(student_id)
    if not student:
        raise HTTPException(404, "الطالب غير موجود")
    if not project.group_id or student.group_id != project.group_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "الطالب ليس ضمن مجموعة هذا المشروع")

    if category not in VALID_CATEGORIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"الفئة غير صالحة. المتاح: {', '.join(sorted(VALID_CATEGORIES))}")
    if not 0 <= score <= 25:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "الدرجة يجب أن تكون بين 0 و 25")

    grade = grade_repo.upsert(
        student_id=student_id, project_id=project_id, supervisor_id=supervisor_id,
        category=category, score=score, max_score=25.0, feedback=feedback,
    )
    db.commit()
    db.refresh(grade)
    return grade


def grade_student_bulk(
    db: Session, *, supervisor_id: int, student_id: int,
    project_id: int, scores: dict[str, float], feedback: str | None = None,
):
    results = []
    for cat in GradeCategory:
        cat_score = scores.get(cat.value)
        if cat_score is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"الدرجة مطلوبة للفئة: {cat.value}")
        g = grade_student(
            db, supervisor_id=supervisor_id, student_id=student_id,
            project_id=project_id, category=cat.value, score=cat_score, feedback=feedback,
        )
        results.append(g)
    return results


def get_student_grades(db: Session, student_id: int, project_id: int) -> dict:
    user_repo = UserRepository(db)
    grade_repo = GradeRepository(db)

    student = user_repo.get_by_id(student_id)
    if not student:
        raise HTTPException(404, "الطالب غير موجود")

    grades = grade_repo.get_student_grades(student_id, project_id)
    total = sum(float(g.score) for g in grades)
    max_total = sum(float(g.max_score) for g in grades)
    all_approved = all(g.approved is True for g in grades) if grades else None

    return {
        "student_id": student_id, "display_id": student.display_id,
        "full_name": student.full_name, "project_id": project_id,
        "total_score": total, "max_total": max_total,
        "categories": [
            {"id": g.id, "category": g.category, "score": float(g.score),
             "max_score": float(g.max_score), "feedback": g.feedback, "approved": g.approved}
            for g in grades
        ],
        "approved": all_approved,
    }


def approve_grade(db: Session, *, coordinator_id: int, grade_id: int, approved: bool):
    user_repo = UserRepository(db)
    grade_repo = GradeRepository(db)

    coord = user_repo.get_by_id(coordinator_id)
    if not coord or coord.role != UserRole.coordinator.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "فقط المنسق يمكنه اعتماد الدرجات")

    grade = grade_repo.get_by_id(grade_id)
    if not grade:
        raise HTTPException(404, "الدرجة غير موجودة")

    grade.approved = approved
    db.commit()
    db.refresh(grade)
    return grade
