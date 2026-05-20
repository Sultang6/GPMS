"""
GPMS Repository Layer — Data Access Only.
All repos use instance pattern: repo = XxxRepository(db); repo.method()
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditLog, FileRecord, Grade, Group, Message,
    Notification, Project, Submission, User,
)


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db


# ──────────────────────────── User ──────────────────────────────

class UserRepository(BaseRepository):

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_display_id(self, display_id: str) -> User | None:
        return self.db.scalar(select(User).where(User.display_id == display_id))

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def list_all(
        self,
        role: str | None = None,
        major: str | None = None,
        search: str | None = None,
    ) -> list[User]:
        stmt = select(User)
        if role:
            stmt = stmt.where(User.role == role)
        if major:
            stmt = stmt.where(User.major == major)
        if search:
            pat = f"%{search}%"
            stmt = stmt.where(
                User.full_name.ilike(pat) | User.email.ilike(pat) | User.display_id.ilike(pat)
            )
        return list(self.db.scalars(stmt.order_by(User.id)).all())

    def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user: User, **kwargs) -> User:
        for k, v in kwargs.items():
            setattr(user, k, v)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def count(self, role: str | None = None) -> int:
        stmt = select(func.count()).select_from(User)
        if role:
            stmt = stmt.where(User.role == role)
        return self.db.scalar(stmt) or 0

    def generate_display_id(self, role: str) -> str:
        cnt = self.count(role)
        seq = cnt + 1
        if role == "Student":
            return f"STD-{datetime.now(timezone.utc).year}-{seq:04d}"
        if role == "Supervisor":
            return f"SUP-{seq:04d}"
        return f"CO-{seq:04d}"


# ──────────────────────────── Group ─────────────────────────────

class GroupRepository(BaseRepository):

    def get_by_id(self, group_id: int) -> Group | None:
        return self.db.get(Group, group_id)

    def list_all(self) -> list[Group]:
        return list(self.db.scalars(select(Group).order_by(Group.id)).all())

    def create(self, **kwargs) -> Group:
        group = Group(**kwargs)
        self.db.add(group)
        self.db.flush()
        return group

    def member_count(self, group_id: int) -> int:
        return self.db.scalar(
            select(func.count()).select_from(User).where(User.group_id == group_id)
        ) or 0

    def get_members(self, group_id: int) -> list[User]:
        return list(self.db.scalars(
            select(User).where(User.group_id == group_id).order_by(User.id)
        ).all())


# ──────────────────────────── Project ───────────────────────────

class ProjectRepository(BaseRepository):

    def get_by_id(self, project_id: int) -> Project | None:
        return self.db.get(Project, project_id)

    def list_all(self, status: str | None = None, supervisor_id: int | None = None) -> list[Project]:
        stmt = select(Project)
        if status:
            stmt = stmt.where(Project.status == status)
        if supervisor_id:
            stmt = stmt.where(Project.supervisor_id == supervisor_id)
        return list(self.db.scalars(stmt.order_by(Project.id)).all())

    def get_by_group(self, group_id: int) -> Project | None:
        return self.db.scalar(select(Project).where(Project.group_id == group_id))

    def create(self, **kwargs) -> Project:
        proj = Project(**kwargs)
        self.db.add(proj)
        self.db.flush()
        return proj

    def update(self, project: Project, **kwargs) -> Project:
        for k, v in kwargs.items():
            setattr(project, k, v)
        self.db.flush()
        return project

    def count(self, status: str | None = None) -> int:
        stmt = select(func.count()).select_from(Project)
        if status:
            stmt = stmt.where(Project.status == status)
        return self.db.scalar(stmt) or 0


# ──────────────────────────── Submission ────────────────────────

class SubmissionRepository(BaseRepository):

    def get_by_id(self, sub_id: int) -> Submission | None:
        return self.db.get(Submission, sub_id)

    def list_by_student(self, student_id: int) -> list[Submission]:
        return list(self.db.scalars(
            select(Submission).where(Submission.student_id == student_id)
            .order_by(Submission.submitted_at.desc())
        ).all())

    def list_by_project(self, project_id: int) -> list[Submission]:
        return list(self.db.scalars(
            select(Submission).where(Submission.project_id == project_id)
            .order_by(Submission.submitted_at.desc())
        ).all())

    def list_by_supervisor(self, supervisor_id: int) -> list[Submission]:
        proj_ids = select(Project.id).where(Project.supervisor_id == supervisor_id)
        return list(self.db.scalars(
            select(Submission).where(Submission.project_id.in_(proj_ids))
            .order_by(Submission.submitted_at.desc())
        ).all())

    def create(self, **kwargs) -> Submission:
        sub = Submission(**kwargs)
        self.db.add(sub)
        self.db.flush()
        return sub

    def update(self, submission: Submission, **kwargs) -> Submission:
        for k, v in kwargs.items():
            setattr(submission, k, v)
        self.db.flush()
        return submission


# ──────────────────────────── Grade ─────────────────────────────

class GradeRepository(BaseRepository):

    def get_by_id(self, grade_id: int) -> Grade | None:
        return self.db.get(Grade, grade_id)

    def find(self, student_id: int, project_id: int, category: str) -> Grade | None:
        return self.db.scalar(
            select(Grade).where(
                Grade.student_id == student_id,
                Grade.project_id == project_id,
                Grade.category == category,
            )
        )

    def get_student_grades(self, student_id: int, project_id: int) -> list[Grade]:
        return list(self.db.scalars(
            select(Grade).where(Grade.student_id == student_id, Grade.project_id == project_id)
            .order_by(Grade.category)
        ).all())

    def upsert(self, *, student_id: int, project_id: int, supervisor_id: int,
               category: str, score: float, max_score: float, feedback: str | None) -> Grade:
        grade = self.find(student_id, project_id, category)
        if grade:
            grade.supervisor_id = supervisor_id
            grade.score = score
            grade.max_score = max_score
            grade.feedback = feedback
            grade.approved = None
        else:
            grade = Grade(
                student_id=student_id, project_id=project_id,
                supervisor_id=supervisor_id, category=category,
                score=score, max_score=max_score, feedback=feedback,
            )
            self.db.add(grade)
        self.db.flush()
        return grade

    def list_by_project(self, project_id: int) -> list[Grade]:
        return list(self.db.scalars(
            select(Grade).where(Grade.project_id == project_id)
            .order_by(Grade.student_id, Grade.category)
        ).all())

    def list_pending_approval(self) -> list[Grade]:
        return list(self.db.scalars(
            select(Grade).where(Grade.approved.is_(None)).order_by(Grade.created_at)
        ).all())

    def approve(self, grade_id: int, approved: bool) -> Grade:
        grade = self.db.get(Grade, grade_id)
        if grade is None:
            raise ValueError(f"Grade {grade_id} not found")
        grade.approved = approved
        self.db.flush()
        return grade


# ──────────────────────────── FileRecord ────────────────────────

class FileRecordRepository(BaseRepository):

    def get_by_id(self, file_id: int) -> FileRecord | None:
        return self.db.get(FileRecord, file_id)

    def get_by_stored_path(self, stored_path: str) -> FileRecord | None:
        return self.db.scalar(select(FileRecord).where(FileRecord.stored_path == stored_path))

    def create(self, **kwargs) -> FileRecord:
        rec = FileRecord(**kwargs)
        self.db.add(rec)
        self.db.flush()
        return rec


# ──────────────────────────── Message ───────────────────────────

class MessageRepository(BaseRepository):

    def list_by_project(self, project_id: int) -> list[Message]:
        return list(self.db.scalars(
            select(Message).where(Message.project_id == project_id).order_by(Message.sent_at)
        ).all())

    def create(self, **kwargs) -> Message:
        msg = Message(**kwargs)
        self.db.add(msg)
        self.db.flush()
        return msg


# ──────────────────────────── Notification ──────────────────────

class NotificationRepository(BaseRepository):

    def list_by_user(self, user_id: int) -> list[Notification]:
        return list(self.db.scalars(
            select(Notification).where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        ).all())

    def get_by_id(self, nid: int) -> Notification | None:
        return self.db.get(Notification, nid)

    def create(self, **kwargs) -> Notification:
        n = Notification(**kwargs)
        self.db.add(n)
        self.db.flush()
        return n

    def mark_all_read(self, user_id: int) -> int:
        from sqlalchemy import update
        result = self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        self.db.flush()
        return result.rowcount


# ──────────────────────────── AuditLog ──────────────────────────

class AuditLogRepository(BaseRepository):

    def list_all(self) -> list[AuditLog]:
        return list(self.db.scalars(
            select(AuditLog).order_by(AuditLog.created_at.desc())
        ).all())

    def create(self, **kwargs) -> AuditLog:
        log = AuditLog(**kwargs)
        self.db.add(log)
        self.db.flush()
        return log
