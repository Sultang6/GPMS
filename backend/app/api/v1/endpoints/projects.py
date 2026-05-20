from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.core.project_access import (
    assert_can_edit_project,
    assert_can_manage_project,
    assert_can_view_project,
    member_dict,
)
from app.core.team_access import assert_team_leader
from app.db.session import get_db
from app.models import Project, Submission, User, UserRole
from app.repositories.repos import GradeRepository, GroupRepository, ProjectRepository
from app.schemas import ProjectCreate, ProjectGradingWeights, ProjectRegister, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


def _project_to_dict(p: Project, db: Session) -> dict:
    supervisor_name = None
    if p.supervisor_id:
        sup = db.get(User, p.supervisor_id)
        if sup:
            supervisor_name = sup.full_name
    student_count = 0
    if p.group_id:
        student_count = (
            db.scalar(
                select(func.count()).select_from(User).where(User.group_id == p.group_id)
            )
            or 0
        )
    return {
        "project_id": p.id,
        "title": p.title,
        "description": p.description,
        "status": p.status,
        "group_id": p.group_id,
        "supervisor_id": p.supervisor_id,
        "supervisor_name": supervisor_name,
        "student_count": student_count,
        "grading_report_weight": float(p.grading_report_weight),
        "grading_individual_weight": float(p.grading_individual_weight),
        "created_at": p.created_at,
    }


def _assert_supervisor_or_coordinator_project(user: User, project: Project) -> None:
    assert_can_manage_project(user, project)


@router.get("")
def list_projects(
    status_filter: str | None = Query(None),
    supervisor_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)

    if current_user.role == UserRole.student.value:
        if not current_user.group_id:
            return []
        proj = db.scalar(
            select(Project).where(Project.group_id == current_user.group_id)
        )
        return [_project_to_dict(proj, db)] if proj else []

    if current_user.role == UserRole.supervisor.value:
        sid = current_user.id
        projects = repo.list_all(status=status_filter, supervisor_id=sid)
        return [_project_to_dict(p, db) for p in projects]

    projects = repo.list_all(status=status_filter, supervisor_id=supervisor_id)
    return [_project_to_dict(p, db) for p in projects]


@router.get("/my")
def get_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)

    if current_user.role == UserRole.student.value:
        if not current_user.group_id:
            return []
        proj = db.scalar(
            select(Project).where(Project.group_id == current_user.group_id)
        )
        return [_project_to_dict(proj, db)] if proj else []

    if current_user.role == UserRole.supervisor.value:
        projects = repo.list_all(supervisor_id=current_user.id)
        return [_project_to_dict(p, db) for p in projects]

    return [_project_to_dict(p, db) for p in repo.list_all()]


@router.post("", status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    repo = ProjectRepository(db)
    project = repo.create(
        title=body.title,
        description=body.description,
        status=body.status,
        supervisor_id=body.supervisor_id,
    )
    db.commit()
    db.refresh(project)
    return _project_to_dict(project, db)


@router.post("/register", status_code=201)
def register_project(
    body: ProjectRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assert_team_leader(db, current_user)

    if not current_user.is_group_leader:
        raise HTTPException(
            status_code=403,
            detail="تسجيل المشروع متاح لقائد الفريق المعرّف من المنسق فقط",
        )

    if not current_user.group_id:
        raise HTTPException(
            status_code=400,
            detail="يجب أن تكون عضواً في مجموعة لتسجيل مشروع",
        )

    existing = db.scalar(
        select(Project).where(Project.group_id == current_user.group_id)
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="مجموعتك مرتبطة بمشروع بالفعل",
        )

    repo = ProjectRepository(db)
    project = repo.create(
        title=body.title,
        description=body.description,
        status="Pending",
        group_id=current_user.group_id,
        supervisor_id=None,
    )
    db.commit()
    db.refresh(project)
    return _project_to_dict(project, db)


@router.get("/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    assert_can_view_project(current_user, project)
    return _project_to_dict(project, db)


@router.patch("/{project_id}")
def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")

    assert_can_edit_project(current_user, project)

    updates = body.model_dump(exclude_unset=True)
    if updates:
        repo.update(project, **updates)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project, db)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    db.delete(project)
    db.commit()
    return None


@router.get("/{project_id}/students")
def get_project_students(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    proj_repo = ProjectRepository(db)
    project = proj_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")

    assert_can_view_project(current_user, project)

    if not project.group_id:
        return []

    grp_repo = GroupRepository(db)
    members = grp_repo.get_members(project.group_id)
    return [member_dict(m, current_user) for m in members]


@router.get("/{project_id}/proposal-file")
def get_project_proposal_file(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """آخر ملف مقترح (Proposal) للمشروع — للعرض من قبل المشرف/المنسق."""
    project = ProjectRepository(db).get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")

    assert_can_manage_project(current_user, project)

    sub = db.scalar(
        select(Submission)
        .where(
            Submission.project_id == project_id,
            Submission.report_type == "Proposal",
        )
        .order_by(Submission.submitted_at.desc())
    )
    if not sub or not sub.file_id:
        return {"file_path": None, "submission_id": None}
    file_path = sub.file.stored_path if sub.file else None
    return {"file_path": file_path, "submission_id": sub.id}


@router.patch("/{project_id}/grading-weights")
def patch_project_grading_weights(
    project_id: int,
    body: ProjectGradingWeights,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Supervisor", "Coordinator")),
):
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    _assert_supervisor_or_coordinator_project(current_user, project)
    repo.update(
        project,
        grading_report_weight=body.grading_report_weight,
        grading_individual_weight=body.grading_individual_weight,
    )
    db.commit()
    db.refresh(project)
    return _project_to_dict(project, db)


@router.get("/{project_id}/grading-sheet")
def get_project_grading_sheet(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Supervisor", "Coordinator")),
):
    proj_repo = ProjectRepository(db)
    project = proj_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    _assert_supervisor_or_coordinator_project(current_user, project)

    students_out: list[dict] = []
    if project.group_id:
        grp_repo = GroupRepository(db)
        grade_repo = GradeRepository(db)
        for m in grp_repo.get_members(project.group_id):
            if m.role != UserRole.student.value:
                continue
            grades = grade_repo.get_student_grades(m.id, project_id)
            ind = next((g for g in grades if g.category == "individual_contribution"), None)
            grp = next((g for g in grades if g.category == "group_report"), None)
            students_out.append(
                {
                    "user_id": m.id,
                    "display_id": m.display_id,
                    "full_name": m.full_name,
                    "individual_score": float(ind.score) if ind else None,
                    "individual_max": float(project.grading_individual_weight),
                    "group_report_score": float(grp.score) if grp else None,
                    "group_report_max": float(project.grading_report_weight),
                }
            )

    return {
        "project_id": project.id,
        "grading_report_weight": float(project.grading_report_weight),
        "grading_individual_weight": float(project.grading_individual_weight),
        "students": students_out,
    }
