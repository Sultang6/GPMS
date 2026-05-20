"""
GPMS Domain Models — Clean Architecture Data Layer
Supports: Groups with Major validation, Individual Grading, Role-specific IDs, File management.
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer,
    Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# ──────────────────────────── Enums ────────────────────────────

class UserRole(str, Enum):
    student = "Student"
    supervisor = "Supervisor"
    coordinator = "Coordinator"

class Major(str, Enum):
    cs = "CS"
    sw = "SW"
    cy = "CY"
    ds = "DS"

class ProjectStatus(str, Enum):
    pending = "Pending"
    approved = "Approved"
    active = "Active"
    completed = "Completed"
    rejected = "Rejected"

class TeamMemberRequestStatus(str, Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"

class ReportType(str, Enum):
    proposal = "Proposal"
    midterm = "Midterm"
    final = "Final"

class GradeCategory(str, Enum):
    report_quality = "report_quality"
    implementation = "implementation"
    documentation = "documentation"
    discussion = "discussion"

# ──────────────────────────── User ─────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    display_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    major: Mapped[str | None] = mapped_column(String(10), nullable=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_group_leader: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    group = relationship("Group", foreign_keys=[group_id], back_populates="members")
    supervised_projects = relationship("Project", foreign_keys="[Project.supervisor_id]", back_populates="supervisor")
    submissions = relationship("Submission", foreign_keys="[Submission.student_id]", back_populates="student")
    grades_received = relationship("Grade", foreign_keys="[Grade.student_id]", back_populates="student")
    grades_given = relationship("Grade", foreign_keys="[Grade.supervisor_id]", back_populates="supervisor")
    sent_messages = relationship("Message", foreign_keys="[Message.sender_id]", back_populates="sender")
    files_uploaded = relationship("FileRecord", foreign_keys="[FileRecord.uploader_id]", back_populates="uploader")
    reference_uploads_contributed = relationship(
        "ReferenceUpload",
        foreign_keys="[ReferenceUpload.uploaded_by_id]",
        back_populates="uploaded_by",
    )
    notifications_received = relationship("Notification", foreign_keys="[Notification.user_id]", back_populates="recipient")
    notifications_sent = relationship("Notification", foreign_keys="[Notification.sender_id]", back_populates="sender")
    audit_logs = relationship("AuditLog", foreign_keys="[AuditLog.user_id]", back_populates="user")

    __table_args__ = (
        Index("ix_users_display_id", "display_id"),
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
        Index("ix_users_group_id", "group_id"),
        Index("ix_users_major", "major"),
    )

# ──────────────────────────── Group ────────────────────────────

class Group(Base):
    """
    A group of students (max 5) who share the SAME major.
    Business Rule: ALL members must have identical major field.
    """
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    major: Mapped[str] = mapped_column(String(10), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    members = relationship("User", foreign_keys="[User.group_id]", back_populates="group")
    project = relationship("Project", back_populates="group", uselist=False)

    member_requests = relationship(
        "TeamMemberRequest",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_groups_major", "major"),
    )


class TeamMemberRequest(Base):
    """طلب إضافة عضو فريق — يقدّمه القائد ويعتمده المنسق بإنشاء الحساب."""

    __tablename__ = "team_member_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    requested_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TeamMemberRequestStatus.pending.value
    )
    coordinator_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    group = relationship("Group", back_populates="member_requests")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approved_user = relationship("User", foreign_keys=[approved_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    __table_args__ = (
        Index("ix_team_member_requests_group_id", "group_id"),
        Index("ix_team_member_requests_status", "status"),
    )

# ──────────────────────────── Project ──────────────────────────

class Project(Base):
    """
    مشروع تخرج.
    grading_report_weight + grading_individual_weight = 100 (يحددهما المشرف/المنسق).
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ProjectStatus.pending.value)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id", ondelete="SET NULL"), unique=True, nullable=True)
    supervisor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    grading_report_weight: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=60)
    grading_individual_weight: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=40)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    group = relationship("Group", back_populates="project")
    supervisor = relationship("User", foreign_keys=[supervisor_id], back_populates="supervised_projects")
    submissions = relationship("Submission", back_populates="project", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="project", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_projects_status", "status"),
        Index("ix_projects_supervisor_id", "supervisor_id"),
        Index("ix_projects_group_id", "group_id"),
    )

# ──────────────────────────── Submission ───────────────────────

class Submission(Base):
    """
    تسليم تقرير من الطالب.
    review_status: pending | graded | revision_requested
    """

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    file_id: Mapped[int | None] = mapped_column(ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    supervisor_grade: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    supervisor_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project = relationship("Project", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id], back_populates="submissions")
    file = relationship("FileRecord", foreign_keys=[file_id])
    graded_by = relationship("User", foreign_keys=[graded_by_id])

    __table_args__ = (
        Index("ix_submissions_project_id", "project_id"),
        Index("ix_submissions_student_id", "student_id"),
    )

# ──────────────────────────── Grade (Individual) ───────────────

class Grade(Base):
    """
    Individual grading: supervisor assigns a score per category per student.
    Categories: report_quality (25), implementation (25), documentation (25), discussion (25) = 100 total.
    """
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    supervisor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=25.0)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student = relationship("User", foreign_keys=[student_id], back_populates="grades_received")
    supervisor = relationship("User", foreign_keys=[supervisor_id], back_populates="grades_given")
    project = relationship("Project", back_populates="grades")

    __table_args__ = (
        UniqueConstraint("student_id", "project_id", "category", name="uq_grade_student_project_category"),
        Index("ix_grades_student_id", "student_id"),
        Index("ix_grades_project_id", "project_id"),
        Index("ix_grades_supervisor_id", "supervisor_id"),
    )

# ──────────────────────────── FileRecord ───────────────────────

class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    uploader = relationship("User", foreign_keys=[uploader_id], back_populates="files_uploaded")
    reference_uploads = relationship("ReferenceUpload", back_populates="file")

    __table_args__ = (
        Index("ix_files_uploader_id", "uploader_id"),
    )


# ──────────────────────────── Reference Upload (shared library) ─

class ReferenceUpload(Base):
    """
    ملفات يشاركها المستخدمون في مكتبة المراجع بعد اعتماد مشرف أو منسق.
    """

    __tablename__ = "reference_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Pending")
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    file = relationship("FileRecord", foreign_keys=[file_id], back_populates="reference_uploads")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id], back_populates="reference_uploads_contributed")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    __table_args__ = (
        Index("ix_reference_uploads_status", "status"),
        Index("ix_reference_uploads_uploaded_by_id", "uploaded_by_id"),
    )


# ──────────────────────────── Message ──────────────────────────

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    project = relationship("Project", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_project_id", "project_id"),
        Index("ix_messages_sender_id", "sender_id"),
    )

# ──────────────────────────── Notification ─────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    recipient = relationship("User", foreign_keys=[user_id], back_populates="notifications_received")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="notifications_sent")

    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
    )

# ──────────────────────────── AuditLog ─────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id], back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
    )

# ──────────────────────────── Chatbot Memory ─────────────────

class ChatbotInteraction(Base):
    """سجل أسئلة المستخدم وإجابات المساعد — للتعلّم التدريجي."""

    __tablename__ = "chatbot_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    norm_question: Mapped[str] = mapped_column(String(500), nullable=False)
    reply: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(80), nullable=False, default="general")
    lang: Mapped[str] = mapped_column(String(5), nullable=False, default="ar")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_chatbot_interactions_user_id", "user_id"),
        Index("ix_chatbot_interactions_norm_question", "norm_question"),
        Index("ix_chatbot_interactions_intent", "intent"),
    )


class ChatbotLearned(Base):
    """إجابات مُثبتة بعد تكرار السؤال — ذاكرة طويلة المدى للمساعد."""

    __tablename__ = "chatbot_learned"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    norm_question: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    sample_question: Mapped[str] = mapped_column(Text, nullable=False)
    reply: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(80), nullable=False, default="general")
    times_asked: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    lang: Mapped[str] = mapped_column(String(5), nullable=False, default="ar")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_chatbot_learned_intent", "intent"),
    )
