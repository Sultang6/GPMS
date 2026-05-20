# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "public" / "pages" / "supervisor" / "supervisor_dashboard.html"
EXTRA_PATH = ROOT / "public" / "js" / "gpms-i18n-extra.js"

D = "<" + "".join(map(chr, [100, 105, 118]))
DE = "</" + "".join(map(chr, [100, 105, 118])) + ">"


def patch_supervisor_html():
    t = TARGET.read_text(encoding="utf-8")
    orig = t

    t = t.replace(
        "tasksList.innerHTML = '"
        + D
        + ' class="text-sm text-slate-500">لا توجد مهام معلقة حالياً.'
        + DE
        + "';",
        "tasksList.innerHTML = `"
        + D
        + ' class="text-sm text-slate-500">${esc(tr("noPendingTasks"))}'
        + DE
        + "`;",
    )

    t = t.replace(
        D + ' class="text-sm font-extrabold text-slate-900">تقرير — مشروع #${esc(s.project_id)}' + DE,
        D
        + ' class="text-sm font-extrabold text-slate-900">${esc(tr("supervisorTaskReport", { id: s.project_id }))}'
        + DE,
    )

    t = t.replace(
        "                    بانتظار المراجعة\n",
        '                    ${esc(tr("statusPendingReview"))}\n',
    )

    t = t.replace(
        '                  الطالب: #${esc(s.student_id)} — النوع: ${esc(s.report_type || "تقرير")} — التاريخ: ${esc(s.submitted_at ? new Date(s.submitted_at).toLocaleDateString("ar-SA") : "—")}',
        '                  ${esc(tr("taskStudentLine", { studentId: s.student_id, type: s.report_type || tr("reportDefaultLabel"), date: s.submitted_at ? new Date(s.submitted_at).toLocaleDateString(window.GPMS_I18N?.getLang?.() === "en" ? "en-US" : "ar-SA") : "—" }))}',
    )

    t = t.replace("<span>مراجعة</span>", "<span>${esc(tr('reviewReport'))}</span>")

    t = t.replace(
        "wrap.innerHTML = '"
        + D
        + ' class="text-sm text-slate-500">لا توجد فرق مرتبطة بمشاريعك بعد.'
        + DE
        + "';",
        "wrap.innerHTML = `"
        + D
        + ' class="text-sm text-slate-500">${esc(tr("noTeamsYet"))}'
        + DE
        + "`;",
    )

    t = t.replace(
        "wrap.innerHTML = '"
        + D
        + ' class="text-sm text-red-600">تعذر تحميل الفرق.'
        + DE
        + "';",
        "wrap.innerHTML = `"
        + D
        + ' class="text-sm text-red-600">${esc(tr("teamsLoadFailed"))}'
        + DE
        + "`;",
    )

    t = t.replace(
        '<span class="font-bold">الأعضاء:</span>',
        '<span class="font-bold">${esc(tr("membersLabel"))}:</span>',
    )

    t = t.replace(
        '${m.is_leader ? " (قائد)" : ""}',
        '${m.is_leader ? " (" + tr("leaderBadge") + ")" : ""}',
    )

    if "const MAJOR_LABEL" in t and "function majorLabel" not in t:
        t = t.replace(
            'const MAJOR_LABEL = { CS: "علوم الحاسب", SW: "هندسة البرمجيات", CY: "الأمن السيبراني", DS: "علوم البيانات" };',
            "function majorLabel(code) {\n"
            '        const k = { CS: "majorCs", SW: "majorSw", CY: "majorCy", DS: "majorDs" }[code];\n'
            "        return k ? tr(k) : code;\n"
            "      }",
        )
        t = t.replace(
            "const major = t.major ? `${MAJOR_LABEL[t.major] || t.major}` : \"—\";",
            'const major = t.major ? majorLabel(t.major) : "—";',
        )

    if "gpms:langchange" not in t:
        t = t.replace(
            "      loadDashboard();\n      loadSupervisorTeams();\n    });",
            "      loadDashboard();\n      loadSupervisorTeams();\n"
            '      document.addEventListener("gpms:langchange", () => {\n'
            "        loadDashboard();\n"
            "        loadSupervisorTeams();\n"
            "      });\n    });",
        )

    if t != orig:
        TARGET.write_text(t, encoding="utf-8", newline="\n")
        print("patched supervisor_dashboard.html")
    else:
        print("no html changes")


def patch_extra_js():
    t = EXTRA_PATH.read_text(encoding="utf-8")
    if "goToCoordinatorView" in t:
        print("extra keys already present")
        return

    t = t.replace(
        "    noPendingTasks: \"لا توجد مهام معلقة حالياً.\",",
        """    goToCoordinatorView: "الانتقال للمنسق (عرض)",
    mySupervisedTeamsHint: "أسماء الفرق وأعضاء كل فريق بعد تسجيلهم من قائد الفريق.",
    newAppointmentRequests: "طلبات حجز موعد جديدة",
    projectCountSub: "عدد المشاريع",
    supervisorTaskReport: "تقرير — مشروع #{id}",
    taskStudentLine: "الطالب: #{studentId} — النوع: {type} — التاريخ: {date}",
    membersLabel: "الأعضاء",
    noTeamsYet: "لا توجد فرق مرتبطة بمشاريعك بعد.",
    teamsLoadFailed: "تعذر تحميل الفرق.",
    noPendingTasks: "لا توجد مهام معلقة حالياً.",""",
    )

    t = t.replace(
        '    noPendingTasks: "No pending tasks at the moment.",',
        """    goToCoordinatorView: "Go to coordinator (view)",
    mySupervisedTeamsHint: "Team names and members after registration by the team leader.",
    newAppointmentRequests: "New appointment requests",
    projectCountSub: "Project count",
    supervisorTaskReport: "Report — project #{id}",
    taskStudentLine: "Student: #{studentId} — Type: {type} — Date: {date}",
    membersLabel: "Members",
    noTeamsYet: "No teams linked to your projects yet.",
    teamsLoadFailed: "Could not load teams.",
    noPendingTasks: "No pending tasks at the moment.",""",
    )

    ui_insert = """    "الانتقال للمنسق (عرض)": "goToCoordinatorView",
    "أسماء الفرق وأعضاء كل فريق بعد تسجيلهم من قائد الفريق.": "mySupervisedTeamsHint",
    "طلبات حجز موعد جديدة": "newAppointmentRequests",
    "عدد المشاريع": "projectCountSub",
    "لا توجد فرق مرتبطة بمشاريعك بعد.": "noTeamsYet",
    "تعذر تحميل الفرق.": "teamsLoadFailed",
    "الأعضاء:": "membersLabel",
"""
    t = t.replace(
        '    "لا يوجد تقارير معلّقة": "noPendingReports",',
        ui_insert + '    "لا يوجد تقارير معلّقة": "noPendingReports",',
    )

    EXTRA_PATH.write_text(t, encoding="utf-8", newline="\n")
    print("patched gpms-i18n-extra.js")


def add_lang_toggle_all_pages():
    pages = ROOT / "public" / "pages"
    n = 0
    for f in pages.rglob("*.html"):
        html = f.read_text(encoding="utf-8")
        if "gpms-lang-toggle.js" in html or "GPMS.js" not in html:
            continue
        new = html.replace(
            '<script src="js/GPMS.js"></script>',
            '<script src="js/GPMS.js"></script>\n    <script src="js/gpms-lang-toggle.js"></script>',
        )
        if new != html:
            f.write_text(new, encoding="utf-8", newline="\n")
            n += 1
            print("lang-toggle:", f.name)
    print("lang-toggle pages:", n)


def patch_nav_spans():
    pages = ROOT / "public" / "pages"
    span_map = [
        ("<span>لوحة التحكم</span>", '<span data-i18n="navDashboard">لوحة التحكم</span>'),
        ("<span>تقييم التقارير</span>", '<span data-i18n="navReviewReports">تقييم التقارير</span>'),
        ("<span>إدخال الدرجات</span>", '<span data-i18n="navEnterGrades">إدخال الدرجات</span>'),
        ("<span>إشعارات الطلاب</span>", '<span data-i18n="navStudentNotifications">إشعارات الطلاب</span>'),
        ("<span>المشاريع المقترحة</span>", '<span data-i18n="navProposedProjects">المشاريع المقترحة</span>'),
        ("<span>المجتمع والمحادثات</span>", '<span data-i18n="navCommunity">المجتمع والمحادثات</span>'),
        ("<span>المساعد الذكي</span>", '<span data-i18n="navChatbot">المساعد الذكي</span>'),
        ("<span>مكتبة المراجع</span>", '<span data-i18n="navReferenceLibrary">مكتبة المراجع</span>'),
    ]
    sidebar_map = [
        (
            D + ' class="text-xs text-slate-300">لوحة تحكم المشرف' + DE,
            D + ' class="text-xs text-slate-300" data-i18n="sidebarSupervisor">لوحة تحكم المشرف' + DE,
        ),
        (
            D + ' class="text-xs text-slate-300">لوحة تحكم الطالب' + DE,
            D + ' class="text-xs text-slate-300" data-i18n="sidebarStudent">لوحة تحكم الطالب' + DE,
        ),
    ]
    n = 0
    for f in pages.rglob("*.html"):
        html = f.read_text(encoding="utf-8")
        orig = html
        for old, new in span_map + sidebar_map:
            if old in html:
                html = html.replace(old, new)
        if html != orig:
            f.write_text(html, encoding="utf-8", newline="\n")
            n += 1
            print("nav:", f.name)
    print("nav pages:", n)


if __name__ == "__main__":
    patch_extra_js()
    patch_nav_spans()
    patch_supervisor_html()
    add_lang_toggle_all_pages()
