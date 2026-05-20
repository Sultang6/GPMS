# -*- coding: utf-8 -*-
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public"

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
    ('<span>تسجيل مشروع تخرج</span>', '<span data-i18n="navRegisterProject">تسجيل مشروع تخرج</span>'),
    ('<span>تسليم التقارير</span>', '<span data-i18n="navSubmitReports">تسليم التقارير</span>'),
    ('<span>الإشعارات</span>', '<span data-i18n="navNotifications">الإشعارات</span>'),
    ('<span>الدرجة النهائية</span>', '<span data-i18n="navFinalGrade">الدرجة النهائية</span>'),
    ('<span>التواصل مع المشرف</span>', '<span data-i18n="navContactSupervisor">التواصل مع المشرف</span>'),
    ('<span>المجتمع والمحادثات</span>', '<span data-i18n="navCommunity">المجتمع والمحادثات</span>'),
    ('<span>المساعد الذكي</span>', '<span data-i18n="navChatbot">المساعد الذكي</span>'),
    ('<span>مكتبة المراجع</span>', '<span data-i18n="navReferenceLibrary">مكتبة المراجع</span>'),
    ('<div class="text-xs text-slate-300">لوحة تحكم المشرف</motion>', '<div class="text-xs text-slate-300" data-i18n="sidebarSupervisor">لوحة تحكم المشرف</div>'),
    ('<div class="gpms-stat-title">إجمالي المشاريع المعتمدة</motion>', '<div class="gpms-stat-title" data-i18n="statApprovedProjects">إجمالي المشاريع المعتمدة</motion>'),
]

# Fix the script - I need ONLY div tags
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
    ('<span>تسجيل مشروع تخرج</span>', '<span data-i18n="navRegisterProject">تسجيل مشروع تخرج</span>'),
    ('<span>تسليم التقارير</span>', '<span data-i18n="navSubmitReports">تسليم التقارير</span>'),
    ('<span>الإشعارات</span>', '<span data-i18n="navNotifications">الإشعارات</span>'),
    ('<span>الدرجة النهائية</span>', '<span data-i18n="navFinalGrade">الدرجة النهائية</span>'),
    ('<span>التواصل مع المشرف</span>', '<span data-i18n="navContactSupervisor">التواصل مع المشرف</span>'),
    ('<span>المجتمع والمحادثات</span>', '<span data-i18n="navCommunity">المجتمع والمحادثات</span>'),
    ('<span>المساعد الذكي</span>', '<span data-i18n="navChatbot">المساعد الذكي</span>'),
    ('<span>مكتبة المراجع</span>', '<span data-i18n="navReferenceLibrary">مكتبة المراجع</span>'),
    ('<span>إضافة توزيع</span>', '<span data-i18n="addAssignment">إضافة توزيع</span>'),
    ('<span>تصدير</span>', '<span data-i18n="export">تصدير</span>'),
    ('<span>تصفية</span>', '<span data-i18n="filter">تصفية</span>'),
    ('<span>فتح المحادثات</span>', '<span data-i18n="openChats">فتح المحادثات</span>'),
    ('<span>الانتقال للمنسق (عرض)</span>', '<span data-i18n="goToCoordinatorView">الانتقال للمنسق (عرض)</span>'),
    ('<div class="text-xs text-slate-300">لوحة تحكم المشرف</div>', '<motion class="text-xs text-slate-300" data-i18n="sidebarSupervisor">لوحة تحكم المشرف</motion>'),
]
