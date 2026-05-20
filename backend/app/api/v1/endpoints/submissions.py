import uuid

from datetime import datetime, timezone

from pathlib import Path



from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from fastapi.responses import FileResponse

from sqlalchemy import select

from sqlalchemy.orm import Session



from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.core.project_access import assert_can_download_file
from app.core.team_access import assert_team_leader
from app.db.session import get_db
from app.models import FileRecord, Notification, Project, Submission, User
from app.repositories.repos import GradeRepository, SubmissionRepository
from app.schemas.schemas import SubmissionGradePatch, SubmissionRevisionRequest
from app.services.file_service import UPLOAD_DIR, _validate_pdf_content

router = APIRouter(prefix="/submissions", tags=["Submissions"])

ALLOWED_MIME = {"application/pdf"}
MAX_SIZE = settings.max_upload_mb * 1024 * 1024





def _submission_to_dict(sub: Submission) -> dict:

    file_path = None

    if sub.file:

        file_path = sub.file.stored_path

    grade_val = float(sub.supervisor_grade) if sub.supervisor_grade is not None else None

    return {

        "submission_id": sub.id,

        "project_id": sub.project_id,

        "student_id": sub.student_id,

        "file_path": file_path,

        "file_id": sub.file_id,

        "report_type": sub.report_type,

        "notes": sub.notes,

        "grade": grade_val,

        "feedback": sub.supervisor_feedback,

        "review_status": sub.review_status,

        "submitted_at": sub.submitted_at,

        "graded_by": sub.graded_by_id,

        "graded_at": sub.graded_at,

        "grade_approved": None,

    }





def _assert_supervisor_or_coordinator_over_project(

    db: Session, sub: Submission, user: User

) -> Project:

    proj = db.get(Project, sub.project_id)

    if proj is None:

        raise HTTPException(status_code=404, detail="المشروع غير موجود")

    if user.role == "Coordinator":

        return proj

    if user.role != "Supervisor" or proj.supervisor_id != user.id:

        raise HTTPException(

            status_code=403,

            detail="لا يمكنك مراجعة تسليمات لمشاريع لا تشرف عليها",

        )

    return proj





def _assert_can_grade_project(db: Session, project_id: int, user: User) -> Project:

    proj = db.get(Project, project_id)

    if proj is None:

        raise HTTPException(status_code=404, detail="المشروع غير موجود")

    if user.role == "Coordinator":

        return proj

    if user.role == "Supervisor" and proj.supervisor_id == user.id:

        return proj

    raise HTTPException(status_code=403, detail="لا يمكنك عرض تقارير هذا المشروع")





def _sync_group_report_grades(

    db: Session,

    *,

    project: Project,

    report_score: float,

    graded_by_id: int,

    feedback: str | None,

) -> None:

    """يطبّق درجة التقرير نفسها على كل طالب في مجموعة المشروع (صنف group_report)."""

    if not project.group_id:

        return

    members = list(

        db.scalars(select(User).where(User.group_id == project.group_id)).all()

    )

    grade_repo = GradeRepository(db)

    max_rep = float(project.grading_report_weight)

    score = float(report_score)

    for m in members:

        if m.role != "Student":

            continue

        grade_repo.upsert(

            student_id=m.id,

            project_id=project.id,

            supervisor_id=graded_by_id,

            category="group_report",

            score=score,

            max_score=max_rep,

            feedback=feedback,

        )





@router.get("/my")

def get_my_submissions(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    repo = SubmissionRepository(db)

    subs = repo.list_by_student(current_user.id)

    return [_submission_to_dict(s) for s in subs]





@router.get("/supervisor")

def get_supervisor_submissions(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    repo = SubmissionRepository(db)

    subs = repo.list_by_supervisor(current_user.id)

    return [_submission_to_dict(s) for s in subs]





@router.get("/for-grade-project/{project_id}")

def list_submissions_for_grading_project(

    project_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("Supervisor", "Coordinator")),

):

    proj = _assert_can_grade_project(db, project_id, current_user)

    stmt = (

        select(Submission)

        .where(Submission.project_id == proj.id)

        .order_by(Submission.submitted_at.desc())

    )

    subs = list(db.scalars(stmt).all())

    return [_submission_to_dict(s) for s in subs]





@router.post("/upload", status_code=201)

def upload_submission(

    file: UploadFile = File(...),

    report_type: str = Form(...),

    notes: str | None = Form(None),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    assert_team_leader(db, current_user)

    if not current_user.group_id:

        raise HTTPException(status_code=400, detail="يجب أن تكون عضواً في مجموعة لرفع التقارير")



    project = db.scalar(

        select(Project).where(Project.group_id == current_user.group_id)

    )

    if not project:

        raise HTTPException(status_code=400, detail="لا يوجد مشروع مرتبط بمجموعتك")



    if file.content_type not in ALLOWED_MIME:

        raise HTTPException(status_code=400, detail="نوع الملف غير مسموح به. يُسمح فقط بملفات PDF")



    content = file.file.read()

    if len(content) > MAX_SIZE:

        raise HTTPException(

            status_code=400,

            detail=f"حجم الملف يتجاوز الحد المسموح ({settings.max_upload_mb} ميجابايت)",

        )

    _validate_pdf_content(content)

    original_name = Path(file.filename or "document.pdf").name

    stored_name = f"{uuid.uuid4().hex}_{original_name}"



    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    (UPLOAD_DIR / stored_name).write_bytes(content)



    file_record = FileRecord(

        original_name=original_name,

        stored_path=stored_name,

        mime_type=file.content_type or "application/pdf",

        size_bytes=len(content),

        uploader_id=current_user.id,

    )

    db.add(file_record)

    db.flush()



    sub_repo = SubmissionRepository(db)

    submission = sub_repo.create(

        project_id=project.id,

        student_id=current_user.id,

        file_id=file_record.id,

        report_type=report_type,

        notes=notes,

    )

    db.commit()

    db.refresh(submission)

    return _submission_to_dict(submission)





@router.get("/download/{filename}")

def download_file(

    filename: str,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    safe_name = Path(filename).name

    record = db.scalar(

        select(FileRecord).where(FileRecord.stored_path == safe_name)

    )

    if not record:

        raise HTTPException(status_code=404, detail="الملف غير موجود")

    assert_can_download_file(db, current_user, record)

    path = UPLOAD_DIR / record.stored_path

    if not path.exists():

        raise HTTPException(status_code=404, detail="الملف غير موجود على الخادم")

    return FileResponse(

        path=str(path),

        filename=record.original_name,

        media_type=record.mime_type,

    )





@router.get("")

def list_submissions(

    project_id: int | None = Query(None),

    graded: bool | None = Query(None),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    stmt = select(Submission).order_by(Submission.submitted_at.desc())

    if project_id is not None:

        _assert_can_grade_project(db, project_id, current_user)

        stmt = stmt.where(Submission.project_id == project_id)

    elif current_user.role != "Coordinator":

        raise HTTPException(

            status_code=403,

            detail="يجب تمرير project_id لعرض التسليمات، أو استخدام حساب منسق.",

        )



    subs = list(db.scalars(stmt).all())

    return [_submission_to_dict(s) for s in subs]





@router.patch("/{submission_id}/grade")

def grade_submission(

    submission_id: int,

    body: SubmissionGradePatch,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("Supervisor", "Coordinator")),

):

    sub_repo = SubmissionRepository(db)

    sub = sub_repo.get_by_id(submission_id)

    if not sub:

        raise HTTPException(status_code=404, detail="التسليم غير موجود")



    proj = _assert_supervisor_or_coordinator_over_project(db, sub, current_user)



    if sub.review_status != "pending":

        raise HTTPException(

            status_code=400,

            detail=(

                "لا يمكن تقييم هذا السجل إلا إذا كان بانتظار المراجعة. "

                "إذا طُلب من الطالب تعديل هذا التسليم، انتظر حتى يُرفع تقرير جديد ثم قيّمه."

            ),

        )



    max_rep = float(proj.grading_report_weight)

    if body.grade < 0 or body.grade > max_rep:

        raise HTTPException(

            status_code=400,

            detail=f"درجة التقرير يجب أن تكون بين 0 و {max_rep} (وزن التقرير الحالي للمشروع).",

        )



    now = datetime.now(timezone.utc)

    sub_repo.update(

        sub,

        supervisor_grade=body.grade,

        supervisor_feedback=body.feedback,

        review_status="graded",

        graded_by_id=current_user.id,

        graded_at=now,

    )

    _sync_group_report_grades(

        db,

        project=proj,

        report_score=body.grade,

        graded_by_id=current_user.id,

        feedback=body.feedback,

    )

    db.commit()

    db.refresh(sub)

    return _submission_to_dict(sub)





@router.patch("/{submission_id}/request-revision")

def request_submission_revision(

    submission_id: int,

    body: SubmissionRevisionRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("Supervisor", "Coordinator")),

):

    sub_repo = SubmissionRepository(db)

    sub = sub_repo.get_by_id(submission_id)

    if not sub:

        raise HTTPException(status_code=404, detail="التسليم غير موجود")



    _assert_supervisor_or_coordinator_over_project(db, sub, current_user)



    if sub.review_status != "pending":

        raise HTTPException(

            status_code=400,

            detail=(

                "يمكن طلب التعديل فقط على تسليم ما يزال بانتظار المراجعة الأولى "

                "(لم يُقيَّم بعد ولم يُطلب تعديله مسبقاً)."

            ),

        )



    fb = body.feedback.strip()

    sub_repo.update(

        sub,

        review_status="revision_requested",

        supervisor_feedback=fb,

        supervisor_grade=None,

        graded_by_id=None,

        graded_at=None,

    )

    db.add(

        Notification(

            user_id=sub.student_id,

            sender_id=current_user.id,

            title="طلب تعديل على التقرير",

            content=f"المشرف طلب منك تعديل تقريرك ({sub.report_type}). الملاحظات: {fb}",

        )

    )

    db.commit()

    db.refresh(sub)

    return _submission_to_dict(sub)





@router.patch("/{submission_id}/approve-grade")

def approve_submission_grade(

    submission_id: int,

    approved: bool = Query(...),

    db: Session = Depends(get_db),

    _current: User = Depends(require_role("Coordinator")),

):

    sub_repo = SubmissionRepository(db)

    sub = sub_repo.get_by_id(submission_id)

    if not sub:

        raise HTTPException(status_code=404, detail="التسليم غير موجود")



    result = _submission_to_dict(sub)

    result["grade_approved"] = approved

    return result

