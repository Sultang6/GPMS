"""Secure file upload / download — PDF only, max 20 MB."""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.repos import FileRecordRepository

UPLOAD_DIR = Path(settings.upload_dir)
MAX_SIZE = settings.max_upload_mb * 1024 * 1024
PDF_MAGIC = b"%PDF"


def _validate_pdf_content(content: bytes) -> None:
    if len(content) < 5 or not content.startswith(PDF_MAGIC):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "الملف ليس PDF صالحاً. يُسمح فقط بملفات PDF حقيقية.",
        )


def save_file(upload_file: UploadFile, uploader_id: int, db: Session):
    if upload_file.content_type not in ("application/pdf",):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "نوع الملف غير مسموح به. يُسمح فقط بملفات PDF")

    content = upload_file.file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "حجم الملف يتجاوز الحد المسموح (20 ميجابايت)")

    _validate_pdf_content(content)

    original_name = Path(upload_file.filename or "document.pdf").name
    if ".." in original_name or "/" in original_name or "\\" in original_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "اسم الملف غير صالح")

    stored_name = f"{uuid.uuid4().hex}_{original_name}"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / stored_name).write_bytes(content)

    repo = FileRecordRepository(db)
    record = repo.create(
        original_name=original_name,
        stored_path=stored_name,
        mime_type=upload_file.content_type or "application/pdf",
        size_bytes=len(content),
        uploader_id=uploader_id,
    )
    db.commit()
    db.refresh(record)
    return record


def get_file_path(file_id_or_name, db: Session) -> Path:
    repo = FileRecordRepository(db)
    record = None

    if isinstance(file_id_or_name, int) or (isinstance(file_id_or_name, str) and file_id_or_name.isdigit()):
        record = repo.get_by_id(int(file_id_or_name))
    else:
        safe = Path(str(file_id_or_name)).name
        record = repo.get_by_stored_path(safe)

    if not record:
        raise HTTPException(404, "الملف غير موجود")

    path = UPLOAD_DIR / record.stored_path
    resolved = path.resolve()
    base = UPLOAD_DIR.resolve()
    if not str(resolved).startswith(str(base)) or not path.exists():
        raise HTTPException(404, "الملف غير موجود على الخادم")
    return path
