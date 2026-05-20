"""GPMS smart assistant — rule engine + DB context + learning memory."""
from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ChatbotInteraction,
    ChatbotLearned,
    Grade,
    Group,
    Message,
    Project,
    ProjectStatus,
    ReportType,
    Submission,
    User,
    UserRole,
)
from app.repositories.repos import GroupRepository, ProjectRepository, UserRepository

SIMILARITY_THRESHOLD = 0.72
LEARN_AFTER_REPEATS = 2

STATIC_INTENTS = frozenset({
    "greeting", "help", "how_to_upload", "how_to_register",
    "deadline", "report_types", "navigation",
})


@dataclass
class ChatbotResult:
    reply: str
    intent: str
    from_memory: bool = False
    interaction_id: int | None = None


def process_message(db: Session, user: User, message: str, lang: str = "ar") -> ChatbotResult:
    _seed_faq_if_empty(db, lang)

    raw = (message or "").strip()
    if not raw:
        return ChatbotResult(
            reply=_t(lang, "empty", "اكتب سؤالك وسأساعدك.", "Type your question and I will help."),
            intent="empty",
        )

    norm = normalize_text(raw)
    intent = detect_intent(norm)

    memory = _lookup_memory(db, norm, intent, lang)
    if memory:
        _record_interaction(db, user.id, raw, norm, memory.reply, intent, lang)
        _strengthen_learned(db, norm, raw, memory.reply, intent, lang)
        interaction_id = _last_interaction_id(db, user.id)
        return ChatbotResult(
            reply=memory.reply,
            intent=intent,
            from_memory=True,
            interaction_id=interaction_id,
        )

    reply = _generate_reply(db, user, norm, intent, lang)
    _record_interaction(db, user.id, raw, norm, reply, intent, lang)
    _strengthen_learned(db, norm, raw, reply, intent, lang)
    interaction_id = _last_interaction_id(db, user.id)
    return ChatbotResult(reply=reply, intent=intent, interaction_id=interaction_id)


def normalize_text(text: str) -> str:
    t = (text or "").strip().lower()
    t = t.replace("\u0640", "")
    for ch in ("إ", "أ", "آ", "ٱ"):
        t = t.replace(ch, "ا")
    t = t.replace("ى", "ي").replace("ة", "ه")
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def token_set(text: str) -> set[str]:
    return {w for w in normalize_text(text).split() if len(w) > 1}


def similarity(a: str, b: str) -> float:
    ta, tb = token_set(a), token_set(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def detect_intent(q: str) -> str:
    if any(k in q for k in ("مرحب", "اهلا", "أهلا", "hello", "hi", "السلام", "صباح", "مساء")):
        return "greeting"
    if any(k in q for k in ("مساعد", "help", "ماذا تستطيع", "what can you", "كيف اسألك")):
        return "help"
    if any(k in q for k in ("كيف ارفع", "how upload", "رفع تقرير", "upload report", "تسليم تقرير")):
        return "how_to_upload"
    if any(k in q for k in ("تسجيل مشروع", "register project", "كيف اسجل", "انشاء فريق", "create team")):
        return "how_to_register"
    if any(k in q for k in ("موعد", "deadline", "متى", "when", "نهائي", "due")):
        return "deadline"
    if any(k in q for k in ("proposal", "midterm", "final", "انواع التقارير", "أنواع التقارير", "report type")):
        return "report_types"
    if any(k in q for k in ("مرجع", "مراجع", "reference", "مكتبه", "مكتبة", "مشاريع سابقة")):
        return "reference"
    if any(k in q for k in ("رسائل", "chat", "محادث", "message")):
        return "messages"
    if any(k in q for k in ("اين", "أين", "where", "صفحة", "page", "انتقل", "go to")):
        return "navigation"
    if any(k in q for k in ("حالة", "status", "مشروعي", "my project")):
        return "project_status"
    if any(k in q for k in ("تقرير", "submission", "تسليم", "رفع", "upload", "review", "مراجعة")):
        return "reports"
    if any(k in q for k in ("درجة", "grade", "تقييم", "feedback", "score")):
        return "grades"
    if any(k in q for k in ("مجموعة", "فريق", "group", "team", "اعضاء", "أعضاء", "members")):
        return "team"
    if any(k in q for k in ("طلاب", "students", "اشراف", "إشراف", "supervis")):
        return "supervisor_students"
    if any(k in q for k in ("احص", "إحصائ", "statistics", "dashboard", "ملخص", "summary", "ارقام", "أرقام")):
        return "coordinator_stats"
    if any(k in q for k in ("مشاريع", "projects", "قائمة")):
        return "projects_list"
    if any(k in q for k in ("مشرف", "supervisor", "تواصل", "contact")):
        return "supervisor_contact"
    if any(k in q for k in ("اشعار", "إشعار", "notification")):
        return "notifications"
    return "general"


def _lookup_memory(db: Session, norm: str, intent: str, lang: str) -> ChatbotLearned | None:
    exact = db.scalar(
        select(ChatbotLearned).where(
            ChatbotLearned.norm_question == norm,
            ChatbotLearned.lang == lang,
        )
    )
    if exact:
        return exact

    if intent not in STATIC_INTENTS:
        return None

    learned = db.scalars(select(ChatbotLearned).where(ChatbotLearned.lang == lang)).all()
    best: ChatbotLearned | None = None
    best_score = 0.0
    for row in learned:
        if row.intent != intent:
            continue
        score = similarity(norm, row.norm_question)
        if score >= SIMILARITY_THRESHOLD and score > best_score:
            best = row
            best_score = score
    return best


def _record_interaction(
    db: Session,
    user_id: int,
    question: str,
    norm: str,
    reply: str,
    intent: str,
    lang: str,
) -> None:
    db.add(
        ChatbotInteraction(
            user_id=user_id,
            question=question,
            norm_question=norm[:500],
            reply=reply,
            intent=intent,
            lang=lang,
        )
    )
    db.commit()


def _strengthen_learned(
    db: Session,
    norm: str,
    sample: str,
    reply: str,
    intent: str,
    lang: str,
) -> None:
    row = db.scalar(
        select(ChatbotLearned).where(
            ChatbotLearned.norm_question == norm,
            ChatbotLearned.lang == lang,
        )
    )
    if row:
        row.times_asked += 1
        if intent in STATIC_INTENTS and row.reply != reply:
            row.reply = reply
        db.commit()
        return

    repeat_count = db.scalar(
        select(func.count(ChatbotInteraction.id)).where(
            ChatbotInteraction.norm_question == norm,
            ChatbotInteraction.lang == lang,
        )
    ) or 0

    if intent in STATIC_INTENTS or repeat_count >= LEARN_AFTER_REPEATS:
        db.add(
            ChatbotLearned(
                norm_question=norm[:500],
                sample_question=sample[:1000],
                reply=reply,
                intent=intent,
                times_asked=repeat_count,
                lang=lang,
            )
        )
        try:
            db.commit()
        except Exception:
            db.rollback()


def _last_interaction_id(db: Session, user_id: int) -> int | None:
    return db.scalar(
        select(ChatbotInteraction.id)
        .where(ChatbotInteraction.user_id == user_id)
        .order_by(ChatbotInteraction.id.desc())
        .limit(1)
    )


def _generate_reply(db: Session, user: User, q: str, intent: str, lang: str) -> str:
    handlers = {
        "greeting": lambda: _greeting(user, lang),
        "help": lambda: _help(user, lang),
        "how_to_upload": lambda: _how_to_upload(lang),
        "how_to_register": lambda: _how_to_register(lang),
        "deadline": lambda: _deadline(db, user, lang),
        "report_types": lambda: _report_types(lang),
        "reference": lambda: _reference_reply(db, lang),
        "messages": lambda: _messages_reply(db, user, lang),
        "navigation": lambda: _navigation(user, lang),
        "notifications": lambda: _notifications_hint(user, lang),
        "supervisor_contact": lambda: _supervisor_contact(lang),
    }
    if intent in handlers:
        return handlers[intent]()

    if user.role == UserRole.student.value:
        return _student_reply(db, user, q, intent, lang)
    if user.role == UserRole.supervisor.value:
        return _supervisor_reply(db, user, q, intent, lang)
    return _coordinator_reply(db, q, intent, lang)


def _greeting(user: User, lang: str) -> str:
    name = (user.full_name or "").split()[0] if user.full_name else ""
    role = user.role
    if lang == "en":
        who = {"Student": "student", "Supervisor": "supervisor", "Coordinator": "coordinator"}.get(role, "user")
        base = f"Hello{', ' + name if name else ''}! I'm the GPMS assistant for {who}s."
        return base + " Ask about your project, reports, grades, deadlines, or references."
    base = f"أهلاً{' يا ' + name if name else ''}! أنا مساعد GPMS الذكي."
    if role == UserRole.student.value:
        return base + " اسألني عن مشروعك، التقارير، الدرجات، المواعيد، أو المراجع."
    if role == UserRole.supervisor.value:
        return base + " اسألني عن مشاريعك، التسليمات، المراجعات، أو الطلاب تحت إشرافك."
    return base + " اسألني عن إحصائيات النظام، المشاريع، الدرجات، أو التوزيع."


def _help(user: User, lang: str) -> str:
    if lang == "en":
        lines = [
            "I can help you with:",
            "• Project status and team members",
            "• Report uploads and review status",
            "• Grades and supervisor feedback",
            "• Reference library and deadlines",
            "• Quick navigation inside GPMS",
            "Tip: the more you ask, the better I remember common questions.",
        ]
        return "\n".join(lines)
    lines = [
        "أستطيع مساعدتك في:",
        "• حالة المشروع وأعضاء الفريق",
        "• رفع التقارير وحالة المراجعة",
        "• الدرجات وملاحظات المشرف",
        "• مكتبة المراجع والمواعيد النهائية",
        "• التنقل السريع داخل GPMS",
        "💡 كلما سألت أكثر، أتذكر أسئلتك الشائعة وأجيب أسرع.",
    ]
    return "\n".join(lines)


def _how_to_upload(lang: str) -> str:
    if lang == "en":
        return (
            "To upload a report:\n"
            "1. Open Student → Submit Reports\n"
            "2. Choose report type (Proposal / Midterm / Final)\n"
            "3. Select a PDF file and submit\n"
            "4. Track review status on the same page\n"
            "Your supervisor will review and may request revisions."
        )
    return (
        "لرفع تقرير:\n"
        "1. افتح: الطالب ← تسليم التقارير\n"
        "2. اختر نوع التقرير (Proposal / Midterm / Final)\n"
        "3. ارفع ملف PDF واضغط إرسال\n"
        "4. تابع حالة المراجعة من نفس الصفحة\n"
        "سيراجع المشرف التقرير وقد يطلب تعديلات."
    )


def _how_to_register(lang: str) -> str:
    if lang == "en":
        return (
            "To register a graduation project:\n"
            "1. Student → Register Project\n"
            "2. Form your team (same major, up to 5 members)\n"
            "3. Submit member requests to the coordinator\n"
            "4. Enter project title and description\n"
            "5. Wait for coordinator/supervisor approval"
        )
    return (
        "لتسجيل مشروع تخرج:\n"
        "1. افتح: الطالب ← تسجيل مشروع تخرج\n"
        "2. كوّن الفريق (نفس التخصص، حتى 5 أعضاء)\n"
        "3. أرسل طلبات الأعضاء للمنسق\n"
        "4. أدخل عنوان المشروع ووصفه\n"
        "5. انتظر اعتماد المنسق/المشرف"
    )


def _deadline(db: Session, user: User, lang: str) -> str:
    if user.role == UserRole.student.value and user.group_id:
        project = db.scalar(select(Project).where(Project.group_id == user.group_id))
        if project:
            pending = db.scalar(
                select(func.count(Submission.id)).where(
                    Submission.project_id == project.id,
                    Submission.student_id == user.id,
                    Submission.review_status.in_(["pending", "revision_requested"]),
                )
            ) or 0
            if lang == "en":
                return (
                    f"Project: {project.title} ({project.status}).\n"
                    "GPMS deadlines follow your department calendar — check notifications "
                    f"and supervisor messages.\nPending reports on your account: {pending}."
                )
            return (
                f"مشروعك: {project.title} (الحالة: {project.status}).\n"
                "المواعيد النهائية تُحدد من القسم — تابع الإشعارات ورسائل المشرف.\n"
                f"تقارير معلّقة لديك: {pending}."
            )
    if lang == "en":
        return (
            "Deadlines in GPMS follow the academic semester plan.\n"
            "Typical flow: Proposal → Midterm → Final report.\n"
            "Check Notifications and contact your supervisor for exact dates."
        )
    return (
        "المواعيد في GPMS تتبع خطة الفصل الدراسي.\n"
        "المسار المعتاد: Proposal ← Midterm ← Final.\n"
        "تابع الإشعارات وتواصل مع مشرفك للمواعيد الدقيقة."
    )


def _report_types(lang: str) -> str:
    types = f"{ReportType.proposal.value}, {ReportType.midterm.value}, {ReportType.final.value}"
    if lang == "en":
        return (
            f"Approved report types: {types}.\n"
            "Proposal: project plan — Midterm: progress — Final: complete deliverable.\n"
            "Upload each as PDF from Submit Reports."
        )
    return (
        f"أنواع التقارير المعتمدة: {types}.\n"
        "Proposal: خطة المشروع — Midterm: التقدم — Final: التسليم النهائي.\n"
        "ارفع كل نوع بصيغة PDF من صفحة تسليم التقارير."
    )


def _navigation(user: User, lang: str) -> str:
    if lang == "en":
        pages = {
            UserRole.student.value: "Dashboard, Submit Reports, Register Project, Final Grade, Contact Supervisor",
            UserRole.supervisor.value: "Dashboard, Review Reports, Enter Grades, Student Notifications",
            UserRole.coordinator.value: "Dashboard, Users, Assignments, Approve Grades, System Reports",
        }
        return f"Quick links for your role: {pages.get(user.role, 'Dashboard')}.\nUse the sidebar to navigate."
    pages = {
        UserRole.student.value: "لوحة الطالب، تسليم التقارير، تسجيل المشروع، الدرجة النهائية، التواصل مع المشرف",
        UserRole.supervisor.value: "لوحة المشرف، تقييم التقارير، إدخال الدرجات، إشعارات الطلاب",
        UserRole.coordinator.value: "لوحة المنسق، المستخدمين، التوزيع، اعتماد الدرجات، تقارير النظام",
    }
    return f"صفحاتك حسب دورك: {pages.get(user.role, 'لوحة التحكم')}.\nاستخدم القائمة الجانبية للتنقل."


def _notifications_hint(user: User, lang: str) -> str:
    if lang == "en":
        return "Open Notifications from the sidebar to see alerts about reports, grades, and deadlines."
    return "افتح صفحة الإشعارات من القائمة الجانبية لمتابعة التنبيهات عن التقارير والدرجات والمواعيد."


def _supervisor_contact(lang: str) -> str:
    if lang == "en":
        return "Open Student → Contact Supervisor to send a message or appointment request."
    return "افتح: الطالب ← التواصل مع المشرف لإرسال رسالة أو طلب موعد."


def _student_reply(db: Session, user: User, q: str, intent: str, lang: str) -> str:
    if not user.group_id:
        return _t(
            lang, "no_group",
            "لا توجد مجموعة مرتبطة بحسابك. ابدأ بتسجيل مشروع وتكوين فريق.",
            "No team linked to your account. Start by registering a project and forming a team.",
        )

    group = db.get(Group, user.group_id)
    project = db.scalar(select(Project).where(Project.group_id == user.group_id)) if group else None

    if not project:
        gname = group.name if group else ""
        return _t(
            lang, "no_project",
            f"أنت في مجموعة ({gname}) لكن لم يُربط مشروع بعد. تواصل مع المشرف أو المنسق.",
            f"You are in team ({gname}) but no project is linked yet. Contact your supervisor or coordinator.",
        )

    sub_count = db.scalar(
        select(func.count(Submission.id)).where(Submission.project_id == project.id)
    ) or 0

    last_sub = db.scalar(
        select(Submission)
        .where(Submission.project_id == project.id, Submission.student_id == user.id)
        .order_by(Submission.submitted_at.desc())
        .limit(1)
    )

    if intent in ("project_status", "general") and any(k in q for k in ("حالة", "status", "مشروع")):
        sup_name = project.supervisor.full_name if project.supervisor else "—"
        if lang == "en":
            return (
                f"Project: {project.title}\n"
                f"Status: {project.status}\n"
                f"Supervisor: {sup_name}\n"
                f"Total submissions: {sub_count}"
            )
        return (
            f"مشروعك: {project.title}\n"
            f"الحالة: {project.status}\n"
            f"المشرف: {sup_name}\n"
            f"إجمالي التسليمات: {sub_count}"
        )

    if intent == "reports" or any(k in q for k in ("تقرير", "رفع", "submission")):
        if last_sub:
            status = getattr(last_sub, "review_status", None) or "pending"
            date_s = last_sub.submitted_at.strftime("%Y-%m-%d") if last_sub.submitted_at else "—"
            if lang == "en":
                return (
                    f"Last report: {last_sub.report_type} on {date_s} (status: {status}).\n"
                    f"Total project submissions: {sub_count}.\n"
                    "Upload more from Submit Reports."
                )
            return (
                f"آخر تقرير: {last_sub.report_type} بتاريخ {date_s} (الحالة: {status}).\n"
                f"إجمالي تسليمات المشروع: {sub_count}.\n"
                "يمكنك رفع المزيد من صفحة تسليم التقارير."
            )
        return _t(
            lang, "no_reports",
            "لم ترفع أي تقرير بعد. اذهب إلى تسليم التقارير واختر PDF.",
            "You have not uploaded any report yet. Go to Submit Reports and choose a PDF.",
        )

    if intent == "grades" or any(k in q for k in ("درجة", "grade", "تقييم")):
        grade_count = db.scalar(
            select(func.count(Grade.id)).where(
                Grade.student_id == user.id, Grade.project_id == project.id
            )
        ) or 0
        total_score = db.scalar(
            select(func.coalesce(func.sum(Grade.score), 0)).where(
                Grade.student_id == user.id, Grade.project_id == project.id
            )
        ) or 0
        if lang == "en":
            return f"Recorded grades: {grade_count}. Total score: {total_score}/100.\nCheck Final Grade page after coordinator approval."
        return f"درجات مسجّلة: {grade_count}. المجموع: {total_score}/100.\nراجع صفحة الدرجة النهائية بعد اعتماد المنسق."

    if intent == "team" or any(k in q for k in ("مجموعة", "فريق", "group", "اعضاء")):
        members = db.scalars(select(User).where(User.group_id == user.group_id)).all()
        names = ", ".join(m.full_name for m in members)
        gname = group.name if group else ""
        if lang == "en":
            return f"Team ({gname}): {names or '—'}.\nMembers must share the same major."
        return f"فريقك ({gname}): {names or '—'}.\nيجب أن يكون التخصص موحّداً لجميع الأعضاء."

    if lang == "en":
        return (
            f"You are in project ({project.title}), status: {project.status}.\n"
            "Ask about reports, grades, team, deadlines, or references."
        )
    return (
        f"أنت ضمن مشروع ({project.title}) وحالته ({project.status}).\n"
        "اسأل عن التقارير، الدرجات، الفريق، المواعيد، أو المراجع."
    )


def _supervisor_reply(db: Session, user: User, q: str, intent: str, lang: str) -> str:
    projects = list(db.scalars(select(Project).where(Project.supervisor_id == user.id)).all())
    if not projects:
        return _t(lang, "no_sup_projects", "لا توجد مشاريع تحت إشرافك حالياً.", "No projects under your supervision yet.")

    pids = [p.id for p in projects]
    pending_grades = db.scalar(
        select(func.count(Grade.id)).where(Grade.project_id.in_(pids), Grade.approved.is_(None))
    ) or 0
    pending_subs = db.scalar(
        select(func.count(Submission.id)).where(
            Submission.project_id.in_(pids),
            Submission.review_status == "pending",
        )
    ) or 0
    total_subs = db.scalar(
        select(func.count(Submission.id)).where(Submission.project_id.in_(pids))
    ) or 0

    if intent == "supervisor_students" or any(k in q for k in ("طلاب", "students")):
        group_ids = [p.group_id for p in projects if p.group_id]
        sc = 0
        if group_ids:
            sc = db.scalar(
                select(func.count(User.id)).where(
                    User.group_id.in_(group_ids), User.role == UserRole.student.value
                )
            ) or 0
        if lang == "en":
            return f"You supervise {len(projects)} project(s) with {sc} student(s) total."
        return f"تشرف على {len(projects)} مشروع/مشاريع بإجمالي {sc} طالب/طالبة."

    if intent == "reports" or any(k in q for k in ("تقرير", "مراجعة", "review")):
        if lang == "en":
            return (
                f"Submissions: {total_subs} total, {pending_subs} pending review.\n"
                f"Grades awaiting approval: {pending_grades}.\n"
                "Open Review Reports to approve or request revision."
            )
        return (
            f"التسليمات: {total_subs} إجمالاً، {pending_subs} بانتظار المراجعة.\n"
            f"درجات بانتظار الاعتماد: {pending_grades}.\n"
            "افتح تقييم التقارير للاعتماد أو طلب تعديل."
        )

    if intent == "projects_list" or any(k in q for k in ("قائمة", "list")):
        titles = "، ".join(p.title for p in projects[:8])
        if lang == "en":
            return f"Your projects: {titles}."
        return f"مشاريعك: {titles}."

    if lang == "en":
        return (
            f"{len(projects)} project(s) under supervision.\n"
            f"{pending_subs} reports pending, {pending_grades} grades awaiting approval."
        )
    return (
        f"لديك {len(projects)} مشروع/مشاريع تحت الإشراف.\n"
        f"{pending_subs} تقرير بانتظار المراجعة، {pending_grades} درجة بانتظار الاعتماد."
    )


def _coordinator_reply(db: Session, q: str, intent: str, lang: str) -> str:
    proj_repo = ProjectRepository(db)
    user_repo = UserRepository(db)
    tp = proj_repo.count()
    comp = proj_repo.count(ProjectStatus.completed.value)
    pending = proj_repo.count(ProjectStatus.pending.value)
    active = proj_repo.count(ProjectStatus.active.value)
    ts = user_repo.count(UserRole.student.value)
    tsup = user_repo.count(UserRole.supervisor.value)
    groups = db.scalar(select(func.count(Group.id))) or 0
    unapproved = db.scalar(select(func.count(Grade.id)).where(Grade.approved.is_(None))) or 0

    if intent == "coordinator_stats" or any(k in q for k in ("احص", "ملخص", "statistics")):
        if lang == "en":
            return (
                f"System summary:\n"
                f"• Projects: {tp} (active {active}, pending {pending}, completed {comp})\n"
                f"• Students: {ts} | Supervisors: {tsup} | Teams: {groups}\n"
                f"• Unapproved grades: {unapproved}"
            )
        return (
            f"ملخص النظام:\n"
            f"• المشاريع: {tp} (نشطة {active}، معلقة {pending}، مكتملة {comp})\n"
            f"• الطلاب: {ts} | المشرفون: {tsup} | الفرق: {groups}\n"
            f"• درجات غير معتمدة: {unapproved}"
        )

    if intent == "projects_list" or any(k in q for k in ("مشاريع", "projects")):
        if lang == "en":
            return f"Projects: total {tp}, pending {pending}, active {active}, completed {comp}."
        return f"المشاريع: الإجمالي {tp}، معلقة {pending}، نشطة {active}، مكتملة {comp}."

    if intent == "grades":
        if lang == "en":
            return f"Grades not yet approved: {unapproved}."
        return f"درجات لم تُعتمد بعد: {unapproved}."

    if lang == "en":
        return (
            f"Overview: {tp} projects ({comp} completed), {ts} students, {tsup} supervisors.\n"
            "Ask about statistics, projects, or grade approval."
        )
    return (
        f"نظرة عامة: {tp} مشروع ({comp} مكتمل)، {ts} طالب، {tsup} مشرف.\n"
        "اسأل عن الإحصائيات، المشاريع، أو اعتماد الدرجات."
    )


def _reference_reply(db: Session, lang: str) -> str:
    completed = db.scalar(
        select(func.count(Project.id)).where(Project.status == ProjectStatus.completed.value)
    ) or 0
    latest = db.scalar(
        select(Project)
        .where(Project.status == ProjectStatus.completed.value)
        .order_by(Project.created_at.desc())
        .limit(1)
    )
    if latest:
        if lang == "en":
            return (
                f"Reference library has {completed} completed project(s).\n"
                f"Latest: {latest.title}.\n"
                "Open Reference Library to browse PDFs."
            )
        return (
            f"مكتبة المراجع تحتوي {completed} مشروع/مشاريع مكتملة.\n"
            f"أحدثها: {latest.title}.\n"
            "افتح مكتبة المراجع لتصفح ملفات PDF."
        )
    return _t(
        lang, "no_refs",
        "لا توجد مشاريع مكتملة في المكتبة حالياً.",
        "No completed projects in the reference library yet.",
    )


def _messages_reply(db: Session, user: User, lang: str) -> str:
    cnt = db.scalar(select(func.count(Message.id)).where(Message.sender_id == user.id)) or 0
    if lang == "en":
        return f"You sent {cnt} message(s) in GPMS.\nOpen Community & Chats for project discussions."
    return f"أرسلت {cnt} رسالة داخل GPMS.\nافتح المجتمع والمحادثات للنقاش مع الفريق والمشرف."


def _t(lang: str, _key: str, ar: str, en: str) -> str:
    return en if lang == "en" else ar


def _seed_faq_if_empty(db: Session, lang: str) -> None:
    exists = db.scalar(select(func.count(ChatbotLearned.id)).where(ChatbotLearned.lang == lang)) or 0
    if exists:
        return
    seeds = [
        ("كيف ارفع تقرير", "how_to_upload"),
        ("how upload report", "how_to_upload"),
        ("ما هو الموعد النهائي", "deadline"),
        ("what is the deadline", "deadline"),
        ("مرحبا", "greeting"),
        ("hello", "greeting"),
        ("مساعدة", "help"),
        ("help", "help"),
    ]
    dummy = _dummy_user()
    handlers = {
        "how_to_upload": lambda: _how_to_upload(lang),
        "deadline": lambda: _deadline(db, dummy, lang),
        "greeting": lambda: _greeting(dummy, lang),
        "help": lambda: _help(dummy, lang),
    }
    for sample, intent in seeds:
        norm = normalize_text(sample)
        if db.scalar(select(ChatbotLearned.id).where(ChatbotLearned.norm_question == norm)):
            continue
        reply = handlers.get(intent, lambda: "")()
        if not reply:
            continue
        db.add(
            ChatbotLearned(
                norm_question=norm,
                sample_question=sample,
                reply=reply,
                intent=intent,
                times_asked=1,
                lang=lang,
            )
        )
    try:
        db.commit()
    except Exception:
        db.rollback()


def _dummy_user() -> User:
    u = User()
    u.id = 0
    u.full_name = ""
    u.role = UserRole.student.value
    return u


# Backward-compatible alias
def generate_reply(db: Session, user: User, message: str, lang: str = "ar") -> str:
    return process_message(db, user, message, lang).reply
