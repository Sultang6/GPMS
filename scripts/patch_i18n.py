# -*- coding: utf-8 -*-
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public" / "pages"

REPLACEMENTS = [
    ('<span>لوحة التحكم</span>', '<span data-i18n="navDashboard">لوحة التحكم</span>'),
    ('<span>إدارة المستخدمين</span>', '<span data-i18n="navUsers">إدارة المستخدمين</span>'),
    ('<span>توزيع المشاريع والإشراف</span>', '<span data-i18n="navAssignments">توزيع المشاريع والإشراف</span>'),
    ('<span>أوزان التقييم ودرجات المشاريع</span>', '<span data-i18n="navProjectGrades">أوزان التقييم ودرجات المشاريع</span>'),
    ('<span>اعتماد الدرجات النهائية</span>', '<span data-i18n="navApproveFinalGrades">اعتماد الدرجات النهائية</span>'),
    ('<span>تقارير النظام</span>', '<span data-i18n="navSystemReports">تقارير النظام</span>'),
    ('<span>تقييم التقارير</span>', '<span data-i18n="navReviewReports">تقييم التقارير</span>'),
    ('<span>إدخال الدرجات</span>', '<span data-i18n="navEnterGrades">إدخال الدرجات</span>'),
    ('<span>إشعارات الطلاب</span>', '<span data-i18n="navStudentNotifications">إشعارات الطلاب</span>'),
    ('<span>المشاريع المقترحة</span>', '<span data-i18n="navProposedProjects">المشاريع المقترحة</span>'),
    ('<span>المجتمع والمحادثات</span>', '<span data-i18n="navCommunity">المجتمع والمحادثات</span>'),
    ('<span>المساعد الذكي</span>', '<span data-i18n="navChatbot">المساعد الذكي</span>'),
    ('<span>مكتبة المراجع</span>', '<span data-i18n="navReferenceLibrary">مكتبة المراجع</span>'),
    ('<span>إضافة توزيع</span>', '<span data-i18n="addAssignment">إضافة توزيع</span>'),
    ('<span>تصدير</span>', '<span data-i18n="export">تصدير</span>'),
    ('<span>تصفية</span>', '<span data-i18n="filter">تصفية</span>'),
    ('<span>فتح المحادثات</span>', '<span data-i18n="openChats">فتح المحادثات</span>'),
    ('<span>الانتقال للمنسق (عرض)</span>', '<span data-i18n="goToCoordinatorView">الانتقال للمنسق (عرض)</span>'),
    ('<div class="text-xs text-slate-300">لوحة تحكم المشرف</div>', '<motion class="text-xs text-slate-300" data-i18n="sidebarSupervisor">لوحة تحكم المشرف</motion>'),
    ('<div class="text-xs text-slate-300">لوحة تحكم المنسق</div>', '<motion class="text-xs text-slate-300" data-i18n="sidebarCoordinator">لوحة تحكم المنسق</motion>'),
    ('<div class="text-xs text-slate-300">لوحة تحكم الطالب</div>', '<motion class="text-xs text-slate-300" data-i18n="sidebarStudent">لوحة تحكم الطالب</motion>'),
    ('<div class="gpms-stat-title">إجمالي المشاريع المعتمدة</div>', '<motion class="gpms-stat-title" data-i18n="statApprovedProjects">إجمالي المشاريع المعتمدة</motion>'),
    ('<div class="gpms-stat-sub">هذا الفصل</div>', '<motion class="gpms-stat-sub" data-i18n="statThisSemester">هذا الفصل</motion>'),
    ('<motion class="gpms-stat-title">عدد المشرفين النشطين</motion>', '<motion class="gpms-stat-title" data-i18n="statActiveSupervisors">عدد المشرفين النشطين</motion>'),
    ('<motion class="gpms-stat-sub">متاحون للإسناد</motion>', '<motion class="gpms-stat-sub" data-i18n="statAvailableForAssignment">متاحون للإسناد</motion>'),
    ('<motion class="gpms-stat-title">مقترحات بانتظار الاعتماد</motion>', '<motion class="gpms-stat-title" data-i18n="statPendingProposals">مقترحات بانتظار الاعتماد</motion>'),
    ('<motion class="gpms-stat-sub">تحتاج متابعة</motion>', '<motion class="gpms-stat-sub" data-i18n="statNeedsFollowUp">تحتاج متابعة</motion>'),
    ('<motion class="gpms-stat-title">إجمالي الطلاب المشاركين</motion>', '<motion class="gpms-stat-title" data-i18n="statEnrolledStudents">إجمالي الطلاب المشاركين</motion>'),
    ('<motion class="gpms-stat-sub">مسجلين في مشاريع</motion>', '<motion class="gpms-stat-sub" data-i18n="statRegisteredInProjects">مسجلين في مشاريع</motion>'),
    ('<motion class="gpms-stat-title">طلاب تحت الإشراف</motion>', '<motion class="gpms-stat-title" data-i18n="statStudentsSupervised">طلاب تحت الإشراف</motion>'),
    ('<motion class="gpms-stat-title">تقارير بانتظار المراجعة</motion>', '<motion class="gpms-stat-title" data-i18n="statPendingReports">تقارير بانتظار المراجعة</motion>'),
    ('<motion class="gpms-stat-sub">تحتاج قرار + ملاحظات</motion>', '<motion class="gpms-stat-sub" data-i18n="statNeedsDecision">تحتاج قرار + ملاحظات</motion>'),
    ('<motion class="gpms-stat-title">مشاريع جاهزة لرصد الدرجة</motion>', '<motion class="gpms-stat-title" data-i18n="statReadyForGrading">مشاريع جاهزة لرصد الدرجة</motion>'),
    ('<motion class="gpms-stat-sub">بانتظار الإدخال</motion>', '<motion class="gpms-stat-sub" data-i18n="statAwaitingEntry">بانتظار الإدخال</motion>'),
    ('<motion class="gpms-stat-title">طلبات حجز موعد جديدة</motion>', '<motion class="gpms-stat-title" data-i18n="newAppointmentRequests">طلبات حجز موعد جديدة</motion>'),
    ('<motion class="gpms-stat-sub">عدد المشاريع</motion>', '<motion class="gpms-stat-sub" data-i18n="projectCountSub">عدد المشاريع</motion>'),
    ('<h2 class="text-base font-extrabold text-slate-900 sm:text-lg">توزيع المشاريع والإشراف</h2>', '<h2 class="text-base font-extrabold text-slate-900 sm:text-lg" data-i18n="sectionAssignments">توزيع المشاريع والإشراف</h2>'),
    ('<p class="mt-1 text-sm text-slate-500">جدول إداري لإدارة الإسناد (واجهة فقط).</p>', '<p class="mt-1 text-sm text-slate-500" data-i18n="sectionAssignmentsHint">جدول إداري لإدارة الإسناد (واجهة فقط).</p>'),
    ('<h2 class="text-base font-extrabold text-slate-900 sm:text-lg">المهام المعلقة (تتطلب منك مراجعة)</h2>', '<h2 class="text-base font-extrabold text-slate-900 sm:text-lg" data-i18n="pendingTasksSection">المهام المعلقة (تتطلب منك مراجعة)</h2>'),
    ('<h2 class="text-base font-extrabold text-slate-900 sm:text-lg">اختصارات</h2>', '<h2 class="text-base font-extrabold text-slate-900 sm:text-lg" data-i18n="shortcuts">اختصارات</h2>'),
    ('<th>عنوان المشروع</th>', '<th data-i18n="thProjectTitle">عنوان المشروع</th>'),
    ('<th>الحالة</th>', '<th data-i18n="thStatus">الحالة</th>'),
    ('<th>المشرف</th>', '<th data-i18n="thSupervisor">المشرف</th>'),
    ('<th>عدد الطلاب</th>', '<th data-i18n="thStudentCount">عدد الطلاب</th>'),
    ('<th>إجراء</th>', '<th data-i18n="thAction">إجراء</th>'),
    ('id="welcomeSub">نظرة عامة على المشاريع والتوزيع والإشراف.', 'id="welcomeSub" data-i18n="subCoordinator">نظرة عامة على المشاريع والتوزيع والإشراف.'),
    ('id="welcomeSub">ملخص لمهام الإشراف والمراجعات المعلقة.', 'id="welcomeSub" data-i18n="subSupervisor">ملخص لمهام الإشراف والمراجعات المعلقة.'),
]

LANG_TOGGLE_SCRIPT = '<script src="../../js/gpms-lang-toggle.js"></script>'


def patch_file(path):
    html = path.read_text(encoding="utf-8")
    orig = html
    for old, new in REPLACEMENTS:
        if old in html:
            html = html.replace(old, new)
    if "gpms-lang-toggle.js" not in html and "GPMS.js" in html:
        html = html.replace(
            '<script src="../../js/GPMS.js"></script>',
            '<script src="../../js/GPMS.js"></script>\n    ' + LANG_TOGGLE_SCRIPT,
        )
    if html != orig:
        path.write_text(html, encoding="utf-8", newline="\n")
        return True
    return False


if __name__ == "__main__":
    n = 0
    for f in PUBLIC.rglob("*.html"):
        if patch_file(f):
            n += 1
            print(f.name)
    print("done", n)
