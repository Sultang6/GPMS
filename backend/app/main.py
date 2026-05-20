from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.core.must_change_password_middleware import MustChangePasswordMiddleware
from app.db.base import Base
from app.db.sqlite_migrate import apply_sqlite_schema_fixes
from app.db.session import engine, get_db
from app.models import AuditLog, User


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        with engine.begin() as conn:
            apply_sqlite_schema_fixes(conn)
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

_cors_kw: dict = {
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": ["Authorization", "Content-Type"],
}
if settings.is_production:
    _cors_kw["allow_origins"] = settings.cors_origin_list
else:
    # التطوير: Live Server (أي منفذ) + فتح HTML مباشرة (origin = null)
    _cors_kw["allow_origins"] = list(set(settings.cors_origin_list + ["null"]))
    _cors_kw["allow_origin_regex"] = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

app.add_middleware(CORSMiddleware, **_cors_kw)

app.add_middleware(MustChangePasswordMiddleware)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}


@app.get(f"{settings.api_v1_prefix}/audit_logs")
def list_audit_logs(
    db: Session = Depends(get_db),
    _current: User = Depends(require_role("Coordinator")),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    logs = list(db.scalars(stmt).all())
    return [
        {
            "log_id": log.id,
            "user_id": log.user_id,
            "action_description": log.action,
            "created_at": log.created_at,
        }
        for log in logs
    ]
