/* global window, getSession, setSession, API_BASE_URL */
/** @typedef {"ar"|"en"} GpmsLang */

const GPMS_LANG_KEY = "gpms_lang_v1";

const GPMS_I18N = {
  ar: {
    appTitle: "نظام إدارة مشاريع التخرج",
    appSubtitle: "Graduation Project Management System",
    loginUserId: "المعرّف أو رقم الحساب",
    loginUserIdPh: "مثال: CO-0001 للمنسق، STD-2026-0001 للطالب، أو البريد",
    loginPassword: "كلمة المرور",
    loginPasswordPh: "ادخل كلمة المرور",
    loginRole: "تسجيل الدخول كـ",
    roleStudent: "طالب",
    roleSupervisor: "مشرف",
    roleCoordinator: "منسق / إدارة القسم",
    loginSubmit: "تسجيل الدخول",
    forgotPassword: "نسيت كلمة المرور؟",
    language: "اللغة",
    langAr: "العربية",
    langEn: "English",
    footerUni: "جامعة حفر الباطن — GPMS",
    welcome: "أهلاً بك!",
    welcomeNamed: "أهلاً بك يا {name}!",
    welcomeEn: "أهلاً بك!",
    welcomeNamedEn: "Welcome, {name}!",
    subStudent: "ملخص حالة مشروعك والمهام التالية المطلوبة.",
    subStudentMember: "أنت عضو في فريق — يمكنك متابعة المشروع والدرجة والمراجع ومراسلة المشرف والمحادثات.",
    subSupervisor: "ملخص لمهام الإشراف والمراجعات المعلقة.",
    subCoordinator: "نظرة عامة على المشاريع والتوزيع والإشراف.",
    idLabel: "المعرّف",
    navDashboard: "لوحة التحكم",
    navLogout: "تسجيل الخروج",
    navCommunity: "المجتمع والمحادثات",
    navChatbot: "المساعد الذكي",
    navReferenceLibrary: "مكتبة المراجع",
    navStudentDashboard: "لوحة الطالب",
    navSupervisorDashboard: "لوحة المشرف",
    navCoordinatorDashboard: "لوحة المنسق",
    navUsers: "إدارة المستخدمين",
    navAssignments: "توزيع المشاريع والإشراف",
    navProjectGrades: "أوزان التقييم ودرجات المشاريع",
    navApproveFinalGrades: "اعتماد الدرجات النهائية",
    navSystemReports: "تقارير النظام",
    navReviewReports: "تقييم التقارير",
    navEnterGrades: "إدخال الدرجات",
    navStudentNotifications: "إشعارات الطلاب",
    navProposedProjects: "المشاريع المقترحة",
    navRegisterProject: "تسجيل مشروع تخرج",
    navSubmitReports: "تسليم التقارير",
    navNotifications: "الإشعارات",
    navFinalGrade: "الدرجة النهائية",
    navContactSupervisor: "التواصل مع المشرف",
    sidebarCoordinator: "إدارة القسم (المنسق)",
    sidebarSupervisor: "لوحة تحكم المشرف",
    sidebarStudent: "لوحة تحكم الطالب",
    badgeCoordinator: "منسق",
    badgeSupervisor: "مشرف",
    badgeStudent: "طالب",
    statApprovedProjects: "إجمالي المشاريع المعتمدة",
    statThisSemester: "هذا الفصل",
    statActiveSupervisors: "عدد المشرفين النشطين",
    statAvailableForAssignment: "متاحون للإسناد",
    statPendingProposals: "مقترحات بانتظار الاعتماد",
    statNeedsFollowUp: "تحتاج متابعة",
    statEnrolledStudents: "إجمالي الطلاب المشاركين",
    statRegisteredInProjects: "مسجلين في مشاريع",
    statStudentsSupervised: "طلاب تحت الإشراف",
    statPendingReports: "تقارير بانتظار المراجعة",
    statNeedsDecision: "تحتاج قرار + ملاحظات",
    statReadyForGrading: "مشاريع جاهزة لرصد الدرجة",
    statAwaitingEntry: "بانتظار الإدخال",
    statProjectStatus: "حالة المشروع",
    statDeadline: "الموعد النهائي",
    statNextTask: "المهمة القادمة",
    sectionAssignments: "توزيع المشاريع والإشراف",
    sectionAssignmentsHint: "جدول إداري لإدارة الإسناد (واجهة فقط).",
    addAssignment: "إضافة توزيع",
    export: "تصدير",
    filter: "تصفية",
    sort: "ترتيب",
    followUp: "متابعة",
    view: "عرض",
    viewFile: "عرض الملف",
    download: "تحميل",
    approve: "اعتماد",
    reject: "رفض",
    requestRevision: "طلب تعديل",
    confirm: "تأكيد",
    send: "إرسال",
    close: "إغلاق",
    save: "حفظ",
    saveGrade: "حفظ التقييم",
    review: "مراجعة",
    loading: "جاري التحميل...",
    noProjects: "لا توجد مشاريع حالياً",
    loadProjectsError: "خطأ في تحميل المشاريع",
    noPendingProposals: "لا توجد مقترحات معلقة حالياً",
    loadFailed: "فشل تحميل البيانات",
    loadError: "حدث خطأ في التحميل",
    openMenu: "فتح القائمة",
    thProjectTitle: "عنوان المشروع",
    thStatus: "الحالة",
    thSupervisor: "المشرف",
    thStudentCount: "عدد الطلاب",
    thAction: "إجراء",
    thStudent: "الطالب",
    thProject: "المشروع",
    thReport: "التقرير",
    thVersion: "الإصدار",
    thDate: "التاريخ",
    thProposal: "المقترح",
    statusApproved: "معتمد",
    statusActive: "نشط",
    statusCompleted: "مكتمل",
    statusPending: "بانتظار",
    statusDelayed: "متأخر",
    statusPendingReview: "بانتظار المراجعة",
    statusGraded: "تم التقييم",
    statusRevisionRequested: "يُطلب التعديل",
    pendingReportsTitle: "تقارير بانتظار المراجعة",
    pendingReportsHint: "استخدم التصفية حسب الحالة.",
    reviewNoteTitle: "ملاحظة",
    reviewNoteBody: "عند الرفض أو طلب التعديل يجب إضافة ملاحظات.",
    proposalsList: "قائمة المقترحات",
    proposalsHint: "يمكن التصفية حسب الحالة.",
    proposedProjectsTitle: "المشاريع المقترحة",
    proposedProjectsHint: "اعتماد أو رفض أو طلب تعديل.",
    reviewReportsTitle: "تقييم التقارير",
    gradeTitle: "اعتماد وتقييم",
    gradeHint: "درجة التقرير ضمن وزن التقرير للمشروع (حد أقصى {max}).",
    gradeNotes: "ملاحظات التقييم (اختياري)",
    revisionTitle: "إرجاع للطالب وطلب تعديل",
    revisionHint: "اشرح التعديلات المطلوبة — لا يمكن ترك هذا الحقل فارغاً.",
    revisionPh: "ما الذي يجب أن يعدّله الطالب في التقرير؟ (5 أحرف على الأقل)",
    requestRevisionBtn: "إرجاع وطلب التعديل",
    reviewReport: "مراجعة التقرير",
    changePassword: "تغيير كلمة المرور",
    changePasswordHint: "لأسباب أمنية يجب تغيير كلمة المرور الافتراضية.",
    changePasswordHintFull: "لأسباب أمنية، يجب تعيين كلمة مرور جديدة قبل المتابعة.",
    currentPassword: "كلمة المرور الحالية",
    newPassword: "كلمة المرور الجديدة",
    confirmPassword: "تأكيد كلمة المرور",
    passwordMinHint: "6 أحرف على الأقل.",
    saveAndContinue: "حفظ ومتابعة",
    headerReferenceLibrary: "مكتبة المراجع",
    headerCommunity: "مجتمع ومحادثات المشروع",
    headerChatbot: "مساعد GPMS الذكي",
    returnRevisionShort: "إرجاع وطلب التعديل",
    rejectReasonPh: "سبب الرفض / ملاحظات التعديل...",
  },
  en: {
    appTitle: "Graduation Project Management System",
    appSubtitle: "GPMS — University of Hafr Al-Batin",
    loginUserId: "ID or account number",
    loginUserIdPh: "e.g. CO-0001 (coordinator), STD-2026-0001 (student), or email",
    loginPassword: "Password",
    loginPasswordPh: "Enter your password",
    loginRole: "Sign in as",
    roleStudent: "Student",
    roleSupervisor: "Supervisor",
    roleCoordinator: "Coordinator / Department",
    loginSubmit: "Sign in",
    forgotPassword: "Forgot password?",
    language: "Language",
    langAr: "العربية",
    langEn: "English",
    footerUni: "University of Hafr Al-Batin — GPMS",
    welcome: "Welcome!",
    welcomeNamed: "Welcome, {name}!",
    welcomeEn: "Welcome!",
    welcomeNamedEn: "Welcome, {name}!",
    subStudent: "Your project status and next steps.",
    subStudentMember: "Team member — project, grade, library, supervisor messages, and community.",
    subSupervisor: "Summary of supervision tasks and pending reviews.",
    subCoordinator: "Overview of projects, assignments, and supervision.",
    idLabel: "ID",
    navDashboard: "Dashboard",
    navLogout: "Log out",
    navCommunity: "Community & chats",
    navChatbot: "AI assistant",
    navReferenceLibrary: "Reference library",
    navStudentDashboard: "Student dashboard",
    navSupervisorDashboard: "Supervisor dashboard",
    navCoordinatorDashboard: "Coordinator dashboard",
    navUsers: "User management",
    navAssignments: "Projects & supervision",
    navProjectGrades: "Weights & project grades",
    navApproveFinalGrades: "Final grade approval",
    navSystemReports: "System reports",
    navReviewReports: "Review reports",
    navEnterGrades: "Enter grades",
    navStudentNotifications: "Student notifications",
    navProposedProjects: "Proposed projects",
    navRegisterProject: "Register graduation project",
    navSubmitReports: "Submit reports",
    navNotifications: "Notifications",
    navFinalGrade: "Final grade",
    navContactSupervisor: "Contact supervisor",
    sidebarCoordinator: "Department (Coordinator)",
    sidebarSupervisor: "Supervisor panel",
    sidebarStudent: "Student panel",
    badgeCoordinator: "Coordinator",
    badgeSupervisor: "Supervisor",
    badgeStudent: "Student",
    statApprovedProjects: "Total approved projects",
    statThisSemester: "This semester",
    statActiveSupervisors: "Active supervisors",
    statAvailableForAssignment: "Available for assignment",
    statPendingProposals: "Proposals awaiting approval",
    statNeedsFollowUp: "Needs follow-up",
    statEnrolledStudents: "Total participating students",
    statRegisteredInProjects: "Registered in projects",
    statStudentsSupervised: "Students supervised",
    statPendingReports: "Reports pending review",
    statNeedsDecision: "Needs decision + notes",
    statReadyForGrading: "Ready for grading",
    statAwaitingEntry: "Awaiting entry",
    statProjectStatus: "Project status",
    statDeadline: "Deadline",
    statNextTask: "Next task",
    sectionAssignments: "Projects & supervision",
    sectionAssignmentsHint: "Administrative assignment table (UI only).",
    addAssignment: "Add assignment",
    export: "Export",
    filter: "Filter",
    sort: "Sort",
    followUp: "Follow up",
    view: "View",
    viewFile: "View file",
    download: "Download",
    approve: "Approve",
    reject: "Reject",
    requestRevision: "Request revision",
    confirm: "Confirm",
    send: "Send",
    close: "Close",
    save: "Save",
    saveGrade: "Save grade",
    review: "Review",
    loading: "Loading...",
    noProjects: "No projects at the moment",
    loadProjectsError: "Failed to load projects",
    noPendingProposals: "No pending proposals",
    loadFailed: "Failed to load data",
    loadError: "Load error",
    openMenu: "Open menu",
    thProjectTitle: "Project title",
    thStatus: "Status",
    thSupervisor: "Supervisor",
    thStudentCount: "Students",
    thAction: "Action",
    thStudent: "Student",
    thProject: "Project",
    thReport: "Report",
    thVersion: "Version",
    thDate: "Date",
    thProposal: "Proposal",
    statusApproved: "Approved",
    statusActive: "Active",
    statusCompleted: "Completed",
    statusPending: "Pending",
    statusDelayed: "Delayed",
    statusPendingReview: "Pending review",
    statusGraded: "Graded",
    statusRevisionRequested: "Revision requested",
    pendingReportsTitle: "Reports pending review",
    pendingReportsHint: "Filter by status.",
    reviewNoteTitle: "Note",
    reviewNoteBody: "Rejection or revision requests require notes.",
    proposalsList: "Proposals list",
    proposalsHint: "Filter by status.",
    proposedProjectsTitle: "Proposed projects",
    proposedProjectsHint: "Approve, reject, or request revision.",
    reviewReportsTitle: "Review reports",
    gradeTitle: "Approve & grade",
    gradeHint: "Report score within project report weight (max {max}).",
    gradeNotes: "Grading notes (optional)",
    revisionTitle: "Return to student for revision",
    revisionHint: "Explain required changes — cannot be empty.",
    revisionPh: "What should the student change? (min. 5 characters)",
    requestRevisionBtn: "Return & request revision",
    reviewReport: "Review report",
    changePassword: "Change password",
    changePasswordHint: "You must change the default password for security.",
    changePasswordHintFull: "For security, set a new password before continuing.",
    currentPassword: "Current password",
    newPassword: "New password",
    confirmPassword: "Confirm password",
    passwordMinHint: "At least 6 characters.",
    saveAndContinue: "Save & continue",
    headerReferenceLibrary: "Reference library",
    headerCommunity: "Project community & chats",
    headerChatbot: "GPMS AI assistant",
    returnRevisionShort: "Return & request revision",
    rejectReasonPh: "Rejection reason / revision notes...",
  },
};

/** ترجمة عناصر القائمة الجانبية حسب رابط الصفحة */
const NAV_HREF_KEYS = {
  "/pages/admin/admin_dashboard.html": "navDashboard",
  "/pages/admin/admin_users_management.html": "navUsers",
  "/pages/admin/admin_assignments.html": "navAssignments",
  "/pages/admin/admin_approve_grades.html": "navApproveFinalGrades",
  "/pages/admin/admin_system_reports.html": "navSystemReports",
  "/pages/supervisor/supervisor_dashboard.html": "navDashboard",
  "/pages/supervisor/supervisor_review_reports.html": "navReviewReports",
  "/pages/supervisor/supervisor_student_notifications.html": "navStudentNotifications",
  "/pages/supervisor/supervisor_proposed_projects.html": "navProposedProjects",
  "/pages/supervisor/supervisor_enter_grades.html": "navEnterGrades",
  "/pages/student/student_dashboard.html": "navDashboard",
  "/pages/student/student_project_registration.html": "navRegisterProject",
  "/pages/student/student_submit_reports.html": "navSubmitReports",
  "/pages/student/student_notifications.html": "navNotifications",
  "/pages/student/student_final_grade.html": "navFinalGrade",
  "/pages/student/student_contact_supervisor.html": "navContactSupervisor",
  "/pages/shared/community.html": "navCommunity",
  "/pages/shared/chatbot.html": "navChatbot",
  "/pages/shared/reference_library.html": "navReferenceLibrary",
  "/GPMS.html": null,
};

/** نفس المفاتيح بدون شرطة أولى (بعد تغيير مسارات public) */
Object.keys({ ...NAV_HREF_KEYS }).forEach((path) => {
  if (path.startsWith("/")) {
    NAV_HREF_KEYS[path.slice(1)] = NAV_HREF_KEYS[path];
  }
});

/** خريطة النص الإنجليزي → مفتاح (للتبديل من EN إلى AR) */
let UI_EN_KEYS = {};

function rebuildUiKeyMaps() {
  UI_EN_KEYS = {};
  const en = GPMS_I18N.en || {};
  Object.keys(en).forEach((k) => {
    const v = String(en[k] ?? "").trim();
    if (v) UI_EN_KEYS[v] = k;
  });
}
rebuildUiKeyMaps();

function resolveNavI18nKey(href, isAdminPage) {
  const clean = (href || "").split("#")[0].trim();
  if (!clean || clean.toLowerCase().includes("gpms.html")) return null;
  const norm = clean.startsWith("/") ? clean : `/${clean.replace(/^\.\//, "")}`;
  let key = NAV_HREF_KEYS[norm] || NAV_HREF_KEYS[clean] || NAV_HREF_KEYS[norm.slice(1)];
  if (!key) {
    const file = norm.split("/").pop() || "";
    for (const [path, k] of Object.entries(NAV_HREF_KEYS)) {
      if (k && (path === file || path.endsWith(`/${file}`))) {
        key = k;
        break;
      }
    }
  }
  if (norm.includes("supervisor_enter_grades")) {
    key = isAdminPage ? "navProjectGrades" : "navEnterGrades";
  }
  return key;
}

function lookupI18nKey(text) {
  const raw = (text || "").trim();
  if (!raw) return null;
  return UI_AR_KEYS[raw] || UI_EN_KEYS[raw] || null;
}

function getLang() {
  const v = localStorage.getItem(GPMS_LANG_KEY);
  return v === "en" ? "en" : "ar";
}

function setLang(lang) {
  localStorage.setItem(GPMS_LANG_KEY, lang === "en" ? "en" : "ar");
}

function t(key, vars) {
  const lang = getLang();
  let s = GPMS_I18N[lang]?.[key] ?? GPMS_I18N.ar[key] ?? key;
  if (vars) {
    Object.keys(vars).forEach((k) => {
      s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(vars[k]));
    });
  }
  return s;
}

function applyDocumentDirection() {
  const lang = getLang();
  const html = document.documentElement;
  html.lang = lang === "en" ? "en" : "ar";
  html.dir = lang === "en" ? "ltr" : "rtl";
  document.body?.classList.toggle("gpms-ltr", lang === "en");

  const sidebar = document.getElementById("sidebar");
  if (sidebar && window.matchMedia("(min-width: 1024px)").matches) {
    sidebar.classList.remove("gpms-sidebar-closed", "translate-x-full");
    sidebar.style.transform = "";
  }
}

/** نص عربي ثابت في HTML → مفتاح الترجمة */
const UI_AR_KEYS = {
  "إدارة القسم (المنسق)": "sidebarCoordinator",
  "لوحة تحكم المشرف": "sidebarSupervisor",
  "لوحة تحكم الطالب": "sidebarStudent",
  "إجمالي المشاريع المعتمدة": "statApprovedProjects",
  "هذا الفصل": "statThisSemester",
  "عدد المشرفين النشطين": "statActiveSupervisors",
  "متاحون للإسناد": "statAvailableForAssignment",
  "مقترحات بانتظار الاعتماد": "statPendingProposals",
  "تحتاج متابعة": "statNeedsFollowUp",
  "إجمالي الطلاب المشاركين": "statEnrolledStudents",
  "مسجلين في مشاريع": "statRegisteredInProjects",
  "طلاب تحت الإشراف": "statStudentsSupervised",
  "تقارير بانتظار المراجعة": "statPendingReports",
  "تحتاج قرار + ملاحظات": "statNeedsDecision",
  "مشاريع جاهزة لرصد الدرجة": "statReadyForGrading",
  "بانتظار الإدخال": "statAwaitingEntry",
  "حالة المشروع": "statProjectStatus",
  "الموعد النهائي": "statDeadline",
  "المهمة القادمة": "statNextTask",
  "توزيع المشاريع والإشراف": "sectionAssignments",
  "جدول إداري لإدارة الإسناد (واجهة فقط).": "sectionAssignmentsHint",
  "جدول إداري لإدارة الإسناد.": "sectionAssignmentsHint",
  "إضافة توزيع": "addAssignment",
  "تصدير": "export",
  "تصفية": "filter",
  "ترتيب": "sort",
  "متابعة": "followUp",
  "عرض": "view",
  "عرض الملف": "viewFile",
  "تحميل": "download",
  "اعتماد": "approve",
  "رفض": "reject",
  "طلب تعديل": "requestRevision",
  "تأكيد": "confirm",
  "إرسال": "send",
  "إغلاق": "close",
  "حفظ": "save",
  "حفظ التقييم": "saveGrade",
  "مراجعة": "review",
  "جاري التحميل...": "loading",
  "جارٍ التحميل...": "loading",
  "لا توجد مشاريع حالياً": "noProjects",
  "خطأ في تحميل المشاريع": "loadProjectsError",
  "لا توجد مقترحات معلقة حالياً": "noPendingProposals",
  "فشل تحميل البيانات": "loadFailed",
  "حدث خطأ في التحميل": "loadError",
  "فتح القائمة": "openMenu",
  "عنوان المشروع": "thProjectTitle",
  "الحالة": "thStatus",
  "المشرف": "thSupervisor",
  "عدد الطلاب": "thStudentCount",
  "إجراء": "thAction",
  "إجراءات": "thAction",
  "الطالب": "thStudent",
  "المشروع": "thProject",
  "التقرير": "thReport",
  "الإصدار": "thVersion",
  "التاريخ": "thDate",
  "المقترح": "thProposal",
  "تقييم التقارير": "reviewReportsTitle",
  "قائمة المقترحات": "proposalsList",
  "يمكن التصفية حسب الحالة (واجهة).": "proposalsHint",
  "المشاريع المقترحة": "proposedProjectsTitle",
  "اتخاذ قرار: اعتماد/رفض/طلب تعديل (واجهة).": "proposedProjectsHint",
  "تقارير بانتظار المراجعة": "statPendingReports",
  "استخدم التصفية حسب الحالة (واجهة).": "pendingReportsHint",
  "ملاحظة": "reviewNoteTitle",
  "عند الرفض/طلب التعديل يجب إضافة ملاحظات (سلوك النظام).": "reviewNoteBody",
  "عند الرفض أو طلب التعديل يجب إضافة ملاحظات.": "reviewNoteBody",
  "منسق": "badgeCoordinator",
  "مشرف": "badgeSupervisor",
  "طالب": "badgeStudent",
  "تسجيل الخروج": "navLogout",
  "تسجيل مشروع تخرج": "navRegisterProject",
  "تسليم التقارير": "navSubmitReports",
  "الإشعارات": "navNotifications",
  "الدرجة النهائية": "navFinalGrade",
  "التواصل مع المشرف": "navContactSupervisor",
  "إدارة المستخدمين": "navUsers",
  "مكتبة المراجع": "headerReferenceLibrary",
  "مجتمع ومحادثات المشروع": "headerCommunity",
  "مساعد GPMS الذكي": "headerChatbot",
  "تغيير كلمة المرور": "changePassword",
  "لأسباب أمنية، يجب تعيين كلمة مرور جديدة قبل المتابعة.": "changePasswordHintFull",
  "كلمة المرور الحالية": "currentPassword",
  "6 أحرف على الأقل.": "passwordMinHint",
  "حفظ ومتابعة": "saveAndContinue",
  "إرجاع وطلب التعديل": "returnRevisionShort",
};

function stampI18nKey(el) {
  let key = el.getAttribute("data-i18n") || el.getAttribute("data-i18n-key");
  if (!key) {
    key = lookupI18nKey(el.textContent);
    if (key) el.setAttribute("data-i18n-key", key);
  }
  return key;
}

function translateEl(el) {
  const key = stampI18nKey(el);
  if (key) el.textContent = t(key);
}

function translatePlaceholders() {
  document.querySelectorAll("input[placeholder], textarea[placeholder]").forEach((el) => {
    let key = el.getAttribute("data-i18n-ph");
    if (!key) {
      key = lookupI18nKey(el.getAttribute("placeholder"));
      if (key) el.setAttribute("data-i18n-ph", key);
    }
    if (key) el.placeholder = t(key);
  });
}

function translateLabels() {
  document.querySelectorAll("label, .gpms-section label").forEach((el) => {
    if (el.getAttribute("for") === "gpmsLangSelect" || el.getAttribute("for") === "gpmsLangSelectGlobal") return;
    translateEl(el);
  });
}

function autoTranslateStaticUI() {
  const sel =
    "header h1:not(#welcomeTitle), header p.text-sm, header .text-sm.text-slate-500, " +
    "main h1, main h2, main h3, .gpms-section h2, .gpms-section h3, " +
    ".gpms-section p.text-sm, .gpms-section p.mt-1, .gpms-section .text-sm.font-extrabold, " +
    ".gpms-stat-title, .gpms-stat-sub, table.gpms-table th, .gpms-pill > span, " +
    ".gpms-button:not([type='submit']), aside .leading-tight .text-xs.text-slate-300, " +
    "#chatTitle, #chatSubtitle, .gpms-section .text-xs.text-slate-500";
  document.querySelectorAll(sel).forEach((el) => {
    if (el.id === "welcomeTitle" || el.id === "welcomeSub") return;
    if (el.closest("#gpmsLangGlobalWrap")) return;
    translateEl(el);
  });
  document.querySelectorAll("select option").forEach((opt) => {
    if (opt.hasAttribute("data-i18n")) return;
    const key = lookupI18nKey(opt.textContent);
    if (key) {
      opt.setAttribute("data-i18n-key", key);
      opt.textContent = t(key);
    }
  });
  translateLabels();
  translatePlaceholders();
  translateSidebarByRole();
  document.querySelectorAll("#sidebarToggle").forEach((btn) => {
    btn.setAttribute("aria-label", t("openMenu"));
  });
}

function translateSidebarByRole() {
  const page = document.body?.dataset?.page || "";
  const sub = document.querySelector("aside .leading-tight .text-xs.text-slate-300");
  if (!sub || sub.hasAttribute("data-i18n")) return;
  if (page.startsWith("admin")) sub.textContent = t("sidebarCoordinator");
  else if (page.startsWith("supervisor")) sub.textContent = t("sidebarSupervisor");
  else if (page.startsWith("student")) sub.textContent = t("sidebarStudent");
}

function translatePageTitle() {
  const page = document.body?.dataset?.page || "";
  const suffix = " | GPMS";
  let key = "appTitle";
  if (page.startsWith("admin")) key = "navCoordinatorDashboard";
  else if (page.startsWith("supervisor")) key = "navSupervisorDashboard";
  else if (page.startsWith("student")) key = "navStudentDashboard";
  else if (document.getElementById("loginForm")) {
    document.title = `${t("appTitle")} — GPMS`;
    return;
  }
  document.title = t(key) + suffix;
}

function applyPageTranslations() {
  rebuildUiKeyMaps();
  applyDocumentDirection();
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (!key) return;
    if (el.id === "welcomeTitle") return;
    const val = t(key);
    if (el.hasAttribute("data-i18n-placeholder")) {
      el.placeholder = val;
    } else if (el.hasAttribute("data-i18n-title")) {
      el.title = val;
      el.setAttribute("aria-label", val);
    } else if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
      if (el.getAttribute("placeholder") != null) el.placeholder = val;
    } else {
      el.textContent = val;
    }
  });
  document.querySelectorAll("option[data-i18n]").forEach((opt) => {
    const key = opt.getAttribute("data-i18n");
    if (key) opt.textContent = t(key);
  });
  translateNavigation();
  translateTableHeaders();
  translateRoleBadges();
  autoTranslateStaticUI();
  translatePageTitle();
}

function translateNavigation() {
  const pageRole = document.body?.dataset?.page || "";
  const isAdminPage = pageRole.startsWith("admin");
  document.querySelectorAll("a.gpms-nav-item[href]").forEach((a) => {
    const fullHref = a.getAttribute("href") || "";
    const href = fullHref.split("#")[0];
    const span = a.querySelector("span");
    if (!span) return;
    if (fullHref.toLowerCase().includes("logout")) {
      span.setAttribute("data-i18n-key", "navLogout");
      span.textContent = t("navLogout");
      return;
    }
    const key = resolveNavI18nKey(href, isAdminPage);
    if (key) {
      span.setAttribute("data-i18n-key", key);
      span.textContent = t(key);
    }
  });
}

/** رؤوس الجداول الشائعة عبر data-i18n-th */
function translateTableHeaders() {
  document.querySelectorAll("table.gpms-table th").forEach((th) => {
    translateEl(th);
  });
}

function translateRoleBadges() {
  document.querySelectorAll("[data-i18n-role]").forEach((el) => {
    const role = el.getAttribute("data-i18n-role");
    if (role === "coordinator") el.textContent = t("badgeCoordinator");
    else if (role === "supervisor") el.textContent = t("badgeSupervisor");
    else if (role === "student") el.textContent = t("badgeStudent");
  });
  document.querySelectorAll("[data-i18n-role], [data-student-role-label], header .hidden.sm\\:inline-flex span:last-child").forEach((el) => {
    if (el.hasAttribute("data-student-role-label")) {
      el.textContent = t("badgeStudent");
      return;
    }
    const role = el.getAttribute("data-i18n-role");
    if (role === "coordinator") el.textContent = t("badgeCoordinator");
    else if (role === "supervisor") el.textContent = t("badgeSupervisor");
    else if (role === "student") el.textContent = t("badgeStudent");
    else {
      const k = lookupI18nKey(el.textContent);
      if (k && k.startsWith("badge")) {
        el.setAttribute("data-i18n-key", k);
        el.textContent = t(k);
      }
    }
  });
}

function projectStatusMap() {
  return {
    Approved: { label: t("statusApproved"), cls: "gpms-badge--approved", icon: "badge-check" },
    approved: { label: t("statusApproved"), cls: "gpms-badge--approved", icon: "badge-check" },
    Active: { label: t("statusActive"), cls: "gpms-badge--approved", icon: "badge-check" },
    active: { label: t("statusActive"), cls: "gpms-badge--approved", icon: "badge-check" },
    Completed: { label: t("statusCompleted"), cls: "gpms-badge--approved", icon: "badge-check" },
    completed: { label: t("statusCompleted"), cls: "gpms-badge--approved", icon: "badge-check" },
    Pending: { label: t("statusPending"), cls: "gpms-badge--pending", icon: "clock" },
    pending: { label: t("statusPending"), cls: "gpms-badge--pending", icon: "clock" },
    Delayed: { label: t("statusDelayed"), cls: "gpms-badge--delayed", icon: "alert-triangle" },
    delayed: { label: t("statusDelayed"), cls: "gpms-badge--delayed", icon: "alert-triangle" },
  };
}

function welcomeMessage(name) {
  if (!name) return t("welcome");
  return t("welcomeNamed", { name });
}

function welcomeSubtitle(role, isTeamMember) {
  if (role === "student") {
    return isTeamMember ? t("subStudentMember") : t("subStudent");
  }
  if (role === "supervisor") return t("subSupervisor");
  if (role === "coordinator") return t("subCoordinator");
  return "";
}

async function wirePageWelcome() {
  const titleEl = document.getElementById("welcomeTitle");
  if (!titleEl) return;

  const subEl = document.getElementById("welcomeSub");
  let s = typeof getSession === "function" ? getSession() : null;
  let name = (s?.fullName || "").trim();

  if (!name && s?.accessToken && typeof API_BASE_URL !== "undefined") {
    try {
      const r = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${s.accessToken}` },
      });
      if (r.ok) {
        const me = await r.json();
        name = (me.full_name || "").trim();
        if (typeof setSession === "function") {
          setSession({
            ...s,
            fullName: name,
            displayId: me.display_id || s.displayId,
            isTeamLeader: !!me.is_team_leader,
            isTeamMember: !!me.is_team_member,
          });
          s = getSession();
        }
      }
    } catch {
      /* ignore */
    }
  }

  const lang = getLang();
  titleEl.lang = lang === "en" ? "en" : "ar";
  titleEl.dir = lang === "en" ? "ltr" : "rtl";
  titleEl.textContent = welcomeMessage(name);

  if (subEl && s?.role) {
    let sub = welcomeSubtitle(s.role, s.isTeamMember === true);
    if (s.displayId) {
      sub += lang === "en" ? ` — ${t("idLabel")}: ${s.displayId}` : ` — ${t("idLabel")}: ${s.displayId}`;
    }
    subEl.lang = lang === "en" ? "en" : "ar";
    subEl.dir = lang === "en" ? "ltr" : "rtl";
    subEl.textContent = sub;
  }
}

function wireLoginLanguage() {
  const sel = document.getElementById("gpmsLangSelect");
  if (!sel) return;
  sel.value = getLang();
  sel.addEventListener("change", () => {
    setLang(sel.value);
    applyAllTranslations();
  });
}

async function applyAllTranslations() {
  applyPageTranslations();
  await wirePageWelcome();
  applyPageTranslations();
  document.dispatchEvent(new CustomEvent("gpms:langchange", { detail: { lang: getLang() } }));
}

function wireGlobalLanguageSwitcher() {
  if (document.getElementById("gpmsLangSelectGlobal")) return;

  const header = document.querySelector("header .mx-auto.flex");
  if (!header) return;

  const box = document.createElement("div");
  box.id = "gpmsLangGlobalWrap";
  box.className = "flex shrink-0 items-center gap-2";
  box.innerHTML = `
    <label for="gpmsLangSelectGlobal" class="hidden sm:inline text-xs font-bold text-slate-600">${t("language")}</label>
    <select id="gpmsLangSelectGlobal" class="gpms-input h-10 min-w-[7.5rem] py-1 text-sm font-bold" aria-label="${t("language")}">
      <option value="ar">${GPMS_I18N.ar.langAr}</option>
      <option value="en">${GPMS_I18N.en.langEn}</option>
    </select>
  `;

  const roleBadge = header.querySelector("[data-i18n-role]") || header.querySelector(".hidden.sm\\:inline-flex");
  if (roleBadge) header.insertBefore(box, roleBadge);
  else header.appendChild(box);

  const sel = document.getElementById("gpmsLangSelectGlobal");
  if (!sel) return;
  sel.value = getLang();
  sel.addEventListener("change", () => {
    setLang(sel.value);
    const lbl = box.querySelector("label");
    if (lbl) lbl.textContent = t("language");
    sel.setAttribute("aria-label", t("language"));
    applyAllTranslations();
  });
}

function mergeExtraI18n(extra) {
  if (!extra) return;
  if (extra.ar) Object.assign(GPMS_I18N.ar, extra.ar);
  if (extra.en) Object.assign(GPMS_I18N.en, extra.en);
  if (extra.uiAr) Object.assign(UI_AR_KEYS, extra.uiAr);
  rebuildUiKeyMaps();
}

window.GPMS_I18N = {
  getLang,
  setLang,
  t,
  mergeExtraI18n,
  applyPageTranslations,
  applyDocumentDirection,
  applyAllTranslations,
  wirePageWelcome,
  wireLoginLanguage,
  wireGlobalLanguageSwitcher,
  welcomeMessage,
  projectStatusMap,
  translateNavigation,
};

if (typeof window !== "undefined") {
  if (window.GPMS_I18N_EXTRA) mergeExtraI18n(window.GPMS_I18N_EXTRA);
  else if (window.__GPMS_I18N_EXTRA_PENDING) mergeExtraI18n(window.__GPMS_I18N_EXTRA_PENDING);
}
