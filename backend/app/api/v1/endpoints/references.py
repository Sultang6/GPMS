"""
مكتبة المراجع: مشاريع + ملفات يرفعها الطلاب/الآخرون.
بعد اعتماد المشرف أو المنسق (Approved) تظهر الملفات تلقائياً في قائمة المراجع العامة.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.core.team_access import student_team_context
from app.db.session import get_db
from app.models import Project, ReferenceUpload, User
from app.schemas import ReferenceReviewInput
from app.services.file_service import get_file_path, save_file

router = APIRouter(prefix="/references", tags=["References"])


def _serialize_upload(ru: ReferenceUpload) -> dict:
    fr = ru.file
    ub = ru.uploaded_by
    rb = ru.reviewed_by
    return {
        "id": ru.id,
        "title": ru.title,
        "description": ru.description,
        "status": ru.status,
        "original_filename": fr.original_name if fr else None,
        "created_at": ru.created_at,
        "uploaded_by_name": ub.full_name if ub else "",
        "uploaded_by_display_id": ub.display_id if ub else "",
        "reviewed_at": ru.reviewed_at,
        "review_note": ru.review_note,
        "reviewed_by_name": rb.full_name if rb else None,
    }


def _can_download(upload: ReferenceUpload, user: User) -> bool:
    if upload.status == "Approved":
        return True
    if upload.uploaded_by_id == user.id:
        return True
    if user.role in ("Supervisor", "Coordinator"):
        return True
    return False


@router.get("")
def list_references(
    db: Session = Depends(get_db),
    _current: User = Depends(get_current_user),
):
    stmt = (
        select(Project)
        .where(Project.status.in_(["Completed", "Active"]))
        .order_by(Project.created_at.desc())
    )
    projects = list(db.scalars(stmt).all())
    return [
        {
            "project_id": p.id,
            "title": p.title,
            "description": p.description,
            "status": p.status,
            "group_id": p.group_id,
            "supervisor_id": p.supervisor_id,
            "created_at": p.created_at,
        }
        for p in projects
    ]


@router.get("/library-bundle")
def library_bundle(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    - approved_files: فقط المعتمدة → تظهر للجميع في مكتبة المراجع.
    - pending_review: للمشرف والمنسق فقط لاعتماد أو رفض.
    """
    stmt_p = (
        select(Project)
        .where(Project.status.in_(["Completed", "Active"]))
        .order_by(Project.created_at.desc())
    )
    projects = list(db.scalars(stmt_p).all())

    stmt_a = (
        select(ReferenceUpload)
        .where(ReferenceUpload.status == "Approved")
        .order_by(ReferenceUpload.created_at.desc())
    )
    approved = list(db.scalars(stmt_a).all())

    stmt_m = (
        select(ReferenceUpload)
        .where(ReferenceUpload.uploaded_by_id == current_user.id)
        .order_by(ReferenceUpload.created_at.desc())
    )
    mine = list(db.scalars(stmt_m).all())

    pending_review: list[ReferenceUpload] = []
    if current_user.role in ("Supervisor", "Coordinator"):
        stmt_pen = (
            select(ReferenceUpload)
            .where(ReferenceUpload.status == "Pending")
            .order_by(ReferenceUpload.created_at.asc())
        )
        pending_review = list(db.scalars(stmt_pen).all())

    return {
        "projects": [
            {
                "project_id": p.id,
                "title": p.title,
                "description": p.description,
                "status": p.status,
                "group_id": p.group_id,
                "supervisor_id": p.supervisor_id,
                "created_at": p.created_at,
            }
            for p in projects
        ],
        "approved_files": [_serialize_upload(x) for x in approved],
        "my_uploads": [_serialize_upload(x) for x in mine],
        "pending_review": [_serialize_upload(x) for x in pending_review],
    }


@router.post("/files/upload", status_code=201)
def upload_reference_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """الرفع بحالة Pending — لا يُعرض للجميع إلا بعد اعتماد مشرف أو منسق."""
    team = student_team_context(db, current_user)
    if team["is_team_member"]:
        raise HTTPException(
            status_code=403,
            detail="عضو الفريق يمكنه عرض المراجع المعتمدة فقط. الرفع متاح لقائد الفريق والمشرف والمنسق.",
        )

    t = title.strip()
    if len(t) < 1:
        raise HTTPException(status_code=400, detail="عنوان الملف مطلوب")

    record = save_file(file, current_user.id, db)

    ru = ReferenceUpload(
        title=t[:255],
        description=(description or "").strip() or None,
        file_id=record.id,
        uploaded_by_id=current_user.id,
        status="Pending",
    )
    db.add(ru)
    db.commit()
    db.refresh(ru)
    return _serialize_upload(ru)


@router.patch("/files/{upload_id}/review")
def review_reference_upload(
    upload_id: int,
    body: ReferenceReviewInput,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_role("Supervisor", "Coordinator")),
):
    ru = db.get(ReferenceUpload, upload_id)
    if not ru:
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    if ru.status != "Pending":
        raise HTTPException(status_code=400, detail="تمت معالجة هذا الطلب مسبقاً")

    ru.status = "Approved" if body.approved else "Rejected"
    ru.reviewed_by_id = reviewer.id
    ru.reviewed_at = datetime.now(timezone.utc)
    ru.review_note = (body.note or "").strip() or None
    db.commit()
    db.refresh(ru)
    return _serialize_upload(ru)


@router.get("/files/{upload_id}/download")
def download_reference_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ru = db.get(ReferenceUpload, upload_id)
    if not ru or not ru.file_id:
        raise HTTPException(status_code=404, detail="الملف غير موجود")

    if not _can_download(ru, current_user):
        raise HTTPException(
            status_code=403,
            detail="يُسمح بالتحميل بعد اعتماد المشرف أو المنسق، أو إذا كنت صاحب الرفع",
        )

    path = get_file_path(ru.file_id, db)
    fr = ru.file
    fname = fr.original_name if fr else "reference.pdf"
    return FileResponse(
        path=str(path),
        filename=fname,
        media_type=fr.mime_type if fr else "application/pdf",
    )
