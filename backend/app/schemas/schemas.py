"""
GPMS Pydantic V2 Schemas — Strict Validation Layer
"""
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ──────────────────────────── Auth ─────────────────────────────

class LoginRequest(BaseModel):
    user_id: int | None = None
    display_id: str | None = None
    email: str | None = None
    password: str = Field(min_length=1)
    role: str | None = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    display_id: str
    role: str
    redirect_url: str
    must_change_password: bool = False


# ──────────────────────────── User ─────────────────────────────

RoleValue = Literal["Student", "Supervisor", "Coordinator"]
MajorValue = Literal["CS", "SW", "CY", "DS"]


def normalize_display_id_for_role(
    role: str, raw_display_id: str, *, allow_legacy: bool = False
) -> str:
    """
    للحسابات الجديدة: طالب = 4 أرقام، مشرف/منسق = 5 أرقام.
    عند ``allow_legacy=True`` يُقبل أيضاً المعرفات القديمة (مثل STD-…، CO-…).
    """
    d = raw_display_id.strip()
    if not d:
        raise ValueError("المعرّف مطلوب")

    pure4 = bool(re.fullmatch(r"\d{4}", d))
    pure5 = bool(re.fullmatch(r"\d{5}", d))

    if role == "Student":
        if pure4:
            return d
        if pure5:
            raise ValueError("معرّف الطالب لا يكون من خمسة أرقام؛ استخدم أربعة أرقام.")
        if allow_legacy:
            return d
        raise ValueError("معرّف الطالب يجب أن يكون أربعة أرقام بالضبط.")

    if role in ("Supervisor", "Coordinator"):
        if pure5:
            return d
        if pure4:
            raise ValueError("معرّف المشرف أو المنسق يجب أن يكون خمسة أرقام بالضبط، وليس أربعة.")
        if allow_legacy:
            return d
        raise ValueError("معرّف المشرف أو المنسق يجب أن يكون خمسة أرقام بالضبط.")

    raise ValueError("دور المستخدم غير معروف")


class UserCreate(BaseModel):
    display_id: str = Field(min_length=1, max_length=20)
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=1, max_length=255)
    password: str | None = Field(default=None)
    role: RoleValue
    major: MajorValue | None = None
    is_group_leader: bool = False

    @field_validator("display_id")
    @classmethod
    def strip_display(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_display_major_and_password(self):
        self.display_id = normalize_display_id_for_role(
            self.role, self.display_id, allow_legacy=False
        )
        if self.role == "Student" and self.major is None:
            raise ValueError("يجب تحديد تخصص الطالب (CS, SW, CY, DS)")
        if self.role != "Student":
            self.is_group_leader = False
        if self.password is not None and len(self.password) < 6:
            raise ValueError("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
        return self


class UserUpdate(BaseModel):
    display_id: str | None = None
    full_name: str | None = None
    email: str | None = None
    role: RoleValue | None = None
    major: MajorValue | None = None
    group_id: int | None = None
    is_group_leader: bool | None = None


class GroupAddMemberByDisplayId(BaseModel):
    display_id: str = Field(min_length=1, max_length=20)

    @field_validator("display_id")
    @classmethod
    def strip_optional_display(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class UserOut(BaseModel):
    user_id: int = Field(alias="id")
    display_id: str
    full_name: str
    email: str
    role: str
    major: str | None = None
    group_id: int | None = None
    must_change_password: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)

# ──────────────────────────── Group ────────────────────────────

class GroupCreate(BaseModel):
    """Create a student group. Creator is added automatically if omitted."""

    name: str = Field(min_length=1, max_length=200)
    member_ids: list[int] = Field(default_factory=list)
    member_display_ids: list[str] = Field(default_factory=list)

class GroupAddMember(BaseModel):
    user_id: int


class TeamMemberRequestCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=255)


class TeamMemberRequestApprove(BaseModel):
    display_id: str = Field(min_length=4, max_length=20)
    password: str | None = Field(default=None, min_length=6, max_length=128)


class TeamMemberRequestReject(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class TeamMemberRequestOut(BaseModel):
    id: int
    group_id: int
    group_name: str | None = None
    team_major: str | None = None
    requested_by_id: int
    requested_by_name: str | None = None
    full_name: str
    email: str
    status: str
    coordinator_note: str | None = None
    approved_user_id: int | None = None
    approved_display_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class GroupOut(BaseModel):
    id: int
    name: str
    major: str
    created_by: int
    created_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True

class GroupDetailOut(GroupOut):
    members: list[UserOut] = []

# ──────────────────────────── Project ──────────────────────────

StatusValue = Literal["Pending", "Approved", "Active", "Completed", "Rejected"]

class ProjectRegister(BaseModel):
    """تسجيل مشروع من قائد الفريق — بدون اختيار مشرف (يُعيّنه المنسق لاحقاً)."""

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    supervisor_id: int | None = None
    status: StatusValue = "Pending"

class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: StatusValue | None = None
    supervisor_id: int | None = None


class ProjectGradingWeights(BaseModel):
    grading_report_weight: float = Field(ge=0, le=100)
    grading_individual_weight: float = Field(ge=0, le=100)

    @model_validator(mode="after")
    def sum_must_be_100(self):
        total = self.grading_report_weight + self.grading_individual_weight
        if abs(total - 100) > 0.001:
            raise ValueError("مجموع وزن التقرير والوزن الفردي يجب أن يساوي 100")
        return self


class ProjectOut(BaseModel):
    project_id: int = Field(alias="id")
    title: str
    description: str
    status: str
    group_id: int | None = None
    supervisor_id: int | None = None
    grading_report_weight: float = 60
    grading_individual_weight: float = 40
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

# ──────────────────────────── Submission ───────────────────────

ReportValue = Literal["Proposal", "Midterm", "Final"]

class SubmissionOut(BaseModel):
    submission_id: int = Field(alias="id")
    project_id: int
    student_id: int
    file_id: int | None = None
    report_type: str
    notes: str | None = None
    submitted_at: datetime
    file_path: str | None = None
    review_status: str | None = None
    grade: float | None = None
    feedback: str | None = None

    class Config:
        from_attributes = True
        populate_by_name = True


class SubmissionGradePatch(BaseModel):
    grade: float = Field(ge=0)
    feedback: str | None = Field(None, max_length=8000)


class SubmissionRevisionRequest(BaseModel):
    feedback: str = Field(..., min_length=5, max_length=8000)

# ──────────────────────────── Grade (Individual) ───────────────

CategoryValue = Literal[
    "report_quality",
    "implementation",
    "documentation",
    "discussion",
    "group_report",
    "individual_contribution",
]


class GradeInput(BaseModel):
    """Supervisor grades ONE category for ONE student."""

    student_id: int
    project_id: int
    category: CategoryValue
    score: float = Field(ge=0)
    feedback: str | None = None

class GradeBulkInput(BaseModel):
    """Supervisor grades ALL 4 categories for ONE student at once."""
    student_id: int
    project_id: int
    report_quality: float = Field(ge=0, le=25)
    implementation: float = Field(ge=0, le=25)
    documentation: float = Field(ge=0, le=25)
    discussion: float = Field(ge=0, le=25)
    feedback: str | None = None

class GradeOut(BaseModel):
    id: int
    student_id: int
    project_id: int
    supervisor_id: int
    category: str
    score: float
    max_score: float
    feedback: str | None = None
    approved: bool | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class StudentGradeSummary(BaseModel):
    student_id: int
    display_id: str
    full_name: str
    project_id: int
    total_score: float
    max_total: float
    categories: list[GradeOut]
    approved: bool | None = None

# ──────────────────────────── FileRecord ───────────────────────

class FileOut(BaseModel):
    id: int
    original_name: str
    stored_path: str
    mime_type: str
    size_bytes: int
    uploader_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────── Reference library ────────────────

class ReferenceReviewInput(BaseModel):
    approved: bool
    note: str | None = Field(default=None, max_length=1000)

# ──────────────────────────── Message ──────────────────────────

class MessageCreate(BaseModel):
    sender_id: int
    project_id: int
    content: str = Field(min_length=1)

class MessageOut(BaseModel):
    message_id: int = Field(alias="id")
    sender_id: int
    project_id: int
    content: str
    sent_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

# ──────────────────────────── Notification ─────────────────────

class NotificationCreate(BaseModel):
    user_id: int
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)

class NotificationOut(BaseModel):
    notification_id: int = Field(alias="id")
    user_id: int
    sender_id: int | None = None
    title: str
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

# ──────────────────────────── AuditLog ─────────────────────────

class AuditLogOut(BaseModel):
    log_id: int = Field(alias="id")
    user_id: int
    action_description: str = Field(alias="action")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

# ──────────────────────────── Chatbot ──────────────────────────

class ChatbotRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    lang: str = Field(default="ar", pattern="^(ar|en)$")

class ChatbotResponse(BaseModel):
    reply: str
    intent: str = "general"
    from_memory: bool = False
    interaction_id: int | None = None

# ──────────────────────────── Stats ────────────────────────────

class StatsOut(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    pending_projects: int = 0
    total_students: int = 0
    total_supervisors: int = 0
    total_submissions: int = 0
    pending_grades: int = 0
    total_groups: int = 0
