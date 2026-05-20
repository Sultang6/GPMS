/**
 * إعدادات المسارات والـ API — عدّل apiBaseUrl عند رفع الموقع.
 * siteRoot: "/" عند الرفع على جذر الدومين، أو "/gpms/" داخل مجلد فرعي.
 */
window.GPMS_CONFIG = {
  /** "auto" للتطوير المحلي — غيّر إلى "/" عند الرفع على جذر الدومين */
  siteRoot: "auto",
  apiBaseUrl: "https://gpms-6nww.onrender.com/api/v1",
  logo: "assets/images/uhb-logo.png",

  paths: {
    login: "/GPMS.html",
    changePassword: "/pages/shared/change_password.html",

    studentDashboard: "/pages/student/student_dashboard.html",
    studentRegister: "/pages/student/student_project_registration.html",
    studentReports: "/pages/student/student_submit_reports.html",
    studentNotifications: "/pages/student/student_notifications.html",
    studentGrade: "/pages/student/student_final_grade.html",
    studentContact: "/pages/student/student_contact_supervisor.html",

    supervisorDashboard: "/pages/supervisor/supervisor_dashboard.html",
    supervisorReview: "/pages/supervisor/supervisor_review_reports.html",
    supervisorProposals: "/pages/supervisor/supervisor_proposed_projects.html",
    supervisorGrades: "/pages/supervisor/supervisor_enter_grades.html",
    supervisorNotify: "/pages/supervisor/supervisor_student_notifications.html",

    adminDashboard: "/pages/admin/admin_dashboard.html",
    adminUsers: "/pages/admin/admin_users_management.html",
    adminAssignments: "/pages/admin/admin_assignments.html",
    adminApproveGrades: "/pages/admin/admin_approve_grades.html",
    adminReports: "/pages/admin/admin_system_reports.html",

    community: "/pages/shared/community.html",
    chatbot: "/pages/shared/chatbot.html",
    referenceLibrary: "/pages/shared/reference_library.html",
  },
};

/** جذر مجلد public (حيث css/ و js/ و pages/) */
function gpmsPublicBase() {
  if (location.protocol === "file:") {
    const pageUrl = location.href.split("#")[0].split("?")[0];
    const idx = pageUrl.toLowerCase().indexOf("/pages/");
    if (idx >= 0) return pageUrl.slice(0, idx + 1);
    return pageUrl.slice(0, pageUrl.lastIndexOf("/") + 1);
  }
  const path = location.pathname.replace(/\\/g, "/");
  const pagesIdx = path.indexOf("/pages/");
  if (pagesIdx >= 0) return path.slice(0, pagesIdx + 1);
  const slash = path.lastIndexOf("/");
  return slash >= 0 ? path.slice(0, slash + 1) : "/";
}
window.gpmsPublicBase = gpmsPublicBase;

/** مجلد الصفحة الحالية */
function gpmsPageBase() {
  if (location.protocol === "file:") {
    const pageUrl = location.href.split("#")[0].split("?")[0];
    return pageUrl.slice(0, pageUrl.lastIndexOf("/") + 1);
  }
  const path = location.pathname.replace(/\\/g, "/");
  const slash = path.lastIndexOf("/");
  return slash >= 0 ? path.slice(0, slash + 1) : "/";
}

/** يبني رابط ملف ثابت (شعار، صور) */
function gpmsResolveUrl(relativePath) {
  const rel = String(relativePath || "").replace(/^\//, "");
  const root = window.GPMS_CONFIG?.siteRoot;
  if (root && root !== "auto") {
    const base = root.endsWith("/") ? root : root + "/";
    return base + rel;
  }
  if (location.protocol === "file:") {
    return new URL(rel, gpmsPublicBase()).href;
  }
  return gpmsPublicBase() + rel;
}
window.gpmsResolveUrl = gpmsResolveUrl;
window.gpmsPageBase = gpmsPageBase;

/** روابط الصفحات الداخلية (تبدأ بـ /) — تتكيف مع مجلد public محلياً */
function gpmsHref(pathFromSiteRoot) {
  const path = String(pathFromSiteRoot || "").startsWith("/")
    ? String(pathFromSiteRoot)
    : "/" + String(pathFromSiteRoot || "");
  const root = window.GPMS_CONFIG?.siteRoot;
  if (root && root !== "auto") {
    const base = root.endsWith("/") ? root : root + "/";
    return base + path.slice(1);
  }
  const rel = path.slice(1);
  if (location.protocol === "file:") {
    return new URL(rel, gpmsPublicBase()).href;
  }
  return gpmsPublicBase() + rel;
}
window.gpmsHref = gpmsHref;
