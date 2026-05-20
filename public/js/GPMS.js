/* global lucide */

const GPMS_STORAGE_KEY = "gpms_session_v1";
const API_BASE_URL =
  (typeof window !== "undefined" && window.GPMS_CONFIG?.apiBaseUrl) ||
  "https://gpms-6nww.onrender.com/api/v1";

function gpmsPaths() {
  return window.GPMS_CONFIG?.paths || {};
}

function resolveGpmsHref(path) {
  return typeof window.gpmsHref === "function" ? window.gpmsHref(path) : path;
}

function gpmsLoginUrl() {
  return resolveGpmsHref(gpmsPaths().login || "/GPMS.html");
}

function gpmsChangePasswordUrl() {
  return resolveGpmsHref(gpmsPaths().changePassword || "/pages/shared/change_password.html");
}

function gpmsStudentDashboardUrl() {
  return resolveGpmsHref(gpmsPaths().studentDashboard || "/pages/student/student_dashboard.html");
}

/** ترجمة من أي سكربت صفحة: gpmsTr("navDashboard") */
function gpmsTr(key, vars) {
  return window.GPMS_I18N?.t ? window.GPMS_I18N.t(key, vars) : key;
}
window.gpmsTr = gpmsTr;

const gpmsLangReloadFns = [];
window.gpmsOnLangChange = function (fn) {
  if (typeof fn === "function") gpmsLangReloadFns.push(fn);
};
document.addEventListener("gpms:langchange", () => {
  gpmsLangReloadFns.forEach((fn) => {
    try {
      fn();
    } catch (e) {
      console.warn("gpms lang reload:", e);
    }
  });
});

function getSession() {
  try {
    const raw = localStorage.getItem(GPMS_STORAGE_KEY);
    if (!raw) return null;
    const s = JSON.parse(raw);
    if (!s || typeof s !== "object") return null;
    if (!s.role || !s.accessToken) return null;
    return s;
  } catch {
    return null;
  }
}

function setSession(next) {
  localStorage.setItem(GPMS_STORAGE_KEY, JSON.stringify(next));
}

function clearSession() {
  localStorage.removeItem(GPMS_STORAGE_KEY);
}

function getDefaultDashboardUrl(role) {
  const p = gpmsPaths();
  if (role === "student") {
    return resolveGpmsHref(p.studentDashboard || "/pages/student/student_dashboard.html");
  }
  if (role === "supervisor") {
    return resolveGpmsHref(p.supervisorDashboard || "/pages/supervisor/supervisor_dashboard.html");
  }
  return resolveGpmsHref(p.adminDashboard || "/pages/admin/admin_dashboard.html");
}

/** صفحات مسموحة لعضو الفريق (غير القائد). */
const TEAM_MEMBER_ALLOWED_PAGES = new Set([
  "student_dashboard.html",
  "student_final_grade.html",
  "student_contact_supervisor.html",
  "reference_library.html",
  "community.html",
  "chatbot.html",
  "change_password.html",
]);

/** صفحات مشتركة لكل الطلاب (قائد أو عضو) خارج بادئة student_ */
const STUDENT_SHARED_PAGES = new Set([
  "community.html",
  "chatbot.html",
  "reference_library.html",
]);

const STUDENT_LEADER_ONLY_PAGES = [
  "student_project_registration.html",
  "student_submit_reports.html",
  "student_notifications.html",
];

function isTeamMember() {
  const s = getSession();
  return s?.role === "student" && s.isTeamMember === true;
}

function isTeamLeader() {
  const s = getSession();
  return s?.role === "student" && s.isTeamLeader !== false && !s.isTeamMember;
}

async function refreshStudentTeamAccess() {
  const s = getSession();
  if (!s?.accessToken || s.role !== "student") return s;
  try {
    const r = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${s.accessToken}` },
    });
    if (!r.ok) return s;
    const me = await r.json();
    const next = {
      ...s,
      fullName: me.full_name || s.fullName,
      isTeamLeader: !!me.is_team_leader,
      isTeamMember: !!me.is_team_member,
      isGroupLeaderAccount: !!me.is_group_leader_account,
      teamName: me.team_name || null,
      teamMembers: Array.isArray(me.team_members) ? me.team_members : [],
    };
    setSession(next);
    return next;
  } catch {
    return s;
  }
}

/** إخفاء عناصر القائمة المحجوزة لقائد الفريق فقط. */
function wireStudentTeamNav() {
  const s = getSession();
  if (s?.role !== "student") return;

  const member = isTeamMember();
  const hideLeaderOnly = member || (s.isGroupLeaderAccount === false && !s.isTeamLeader);
  document.querySelectorAll("a.gpms-nav-item[href], a.gpms-pill[href]").forEach((a) => {
    const href = (a.getAttribute("href") || "").toLowerCase();
    const file = href.split("/").pop().split("?")[0];
    if (STUDENT_LEADER_ONLY_PAGES.includes(file)) {
      a.classList.toggle("hidden", hideLeaderOnly);
      if (hideLeaderOnly) a.setAttribute("aria-hidden", "true");
      else a.removeAttribute("aria-hidden");
    }
  });

  document.querySelectorAll("[data-student-leader-only]").forEach((el) => {
    el.classList.toggle("hidden", member);
  });
  document.querySelectorAll("[data-student-member-only]").forEach((el) => {
    el.classList.toggle("hidden", !member);
  });

  const roleBadge = document.querySelector("[data-student-role-label]");
  if (roleBadge) {
    roleBadge.textContent = member ? "عضو فريق" : "طالب / قائد فريق";
  }

  const sidebarSub = document.querySelector("[data-sidebar-student-label]");
  if (sidebarSub) {
    sidebarSub.textContent = member ? "عضو فريق" : "لوحة تحكم الطالب";
  }
}

/** إخفاء روابط لوحات الأدوار غير المناسبة للدور الحالي (من قائمة جانبية أو اختصارات). */
function wireRoleScopedNavLinks() {
  const s = getSession();
  if (!s?.role) return;

  const role = s.role;
  const rules = [
    { pattern: /student_dashboard\.html/i, roles: ["student"] },
    { pattern: /supervisor_dashboard\.html/i, roles: ["supervisor"] },
    { pattern: /admin_dashboard\.html/i, roles: ["coordinator"] },
  ];

  document.querySelectorAll("a[href]").forEach((a) => {
    const href = a.getAttribute("href") || "";
    if (!href || href.startsWith("http")) return;

    for (const { pattern, roles } of rules) {
      if (!pattern.test(href)) continue;
      if (!roles.includes(role)) {
        a.classList.add("hidden");
        a.setAttribute("aria-hidden", "true");
      }
      return;
    }
  });
}

function guardRoutes() {
  const file = (window.location.pathname.split("/").pop() || "").toLowerCase();
  const isLogin = file === "" || file === "index.html" || file === "gpms.html";
  const changePasswordPage = file === "change_password.html";
  const wantsLogout = (window.location.hash || "").toLowerCase() === "#logout";

  if (wantsLogout) {
    clearSession();
    if (!isLogin) window.location.href = gpmsLoginUrl();
    else window.history.replaceState({}, document.title, gpmsLoginUrl());
    return;
  }

  if (isLogin) {
    const s = getSession();
    if (s?.role) {
      window.setTimeout(() => {
        if (s.mustChangePassword) {
          window.location.href = gpmsChangePasswordUrl();
        } else {
          window.location.href = getDefaultDashboardUrl(s.role);
        }
      }, 0);
    }
    return;
  }

  if (changePasswordPage) {
    const s = getSession();
    if (!s?.role) {
      window.location.href = gpmsLoginUrl();
      return;
    }
    if (!s.mustChangePassword) {
      window.location.href = getDefaultDashboardUrl(s.role);
      return;
    }
    return;
  }

  const s = getSession();
  if (!s?.role) {
    window.location.href = gpmsLoginUrl();
    return;
  }

  if (s.mustChangePassword) {
    window.location.href = gpmsChangePasswordUrl();
    return;
  }

  // Optional role mismatch correction (simple guard).
  const role = s.role;
  const isStudentPage = file.startsWith("student_") || file === "student_dashboard.html";
  const isSupervisorPage = file.startsWith("supervisor_") || file === "supervisor_dashboard.html";
  const isAdminPage = file.startsWith("admin_") || file === "admin_dashboard.html";
  const coordinatorGradesPage =
    role === "coordinator" && file === "supervisor_enter_grades.html";

  if (STUDENT_SHARED_PAGES.has(file)) {
    if (role === "student" && isTeamMember() && !TEAM_MEMBER_ALLOWED_PAGES.has(file)) {
      window.location.href = gpmsStudentDashboardUrl();
      return;
    }
    if (role === "student" || role === "supervisor" || role === "coordinator") return;
  }

  if (coordinatorGradesPage) return;

  if (role === "student" && file === "student_project_registration.html") {
    const sess = getSession();
    if (sess?.isTeamMember) {
      try {
        sessionStorage.setItem(
          "gpms_flash",
          "تسجيل المشروع وتكوين الفريق متاح لقائد الفريق فقط."
        );
      } catch {
        /* ignore */
      }
      window.location.href = gpmsStudentDashboardUrl();
      return;
    }
  }

  if (role === "student" && isTeamMember()) {
    if (!TEAM_MEMBER_ALLOWED_PAGES.has(file)) {
      window.location.href = gpmsStudentDashboardUrl();
      return;
    }
    return;
  }

  if (role === "student" && (isStudentPage || STUDENT_SHARED_PAGES.has(file))) {
    return;
  }

  if (
    (role === "student" && !isStudentPage) ||
    (role === "supervisor" && !isSupervisorPage) ||
    (role === "coordinator" && !isAdminPage)
  ) {
    window.location.href = getDefaultDashboardUrl(role);
  }
}

function setFieldError(name, isError) {
  const el = document.querySelector(`[data-error-for="${name}"]`);
  if (!el) return;
  el.classList.toggle("hidden", !isError);
}

function showToast(msg) {
  const toast = document.getElementById("loginToast");
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.remove("hidden");
}

function hideToast() {
  const toast = document.getElementById("loginToast");
  if (!toast) return;
  toast.classList.add("hidden");
  toast.textContent = "";
}

function wirePasswordToggle() {
  const btn = document.getElementById("togglePassword");
  const input = document.getElementById("password");
  if (!btn || !input) return;

  const renderIcon = (isVisible) => {
    btn.setAttribute("aria-label", isVisible ? "إخفاء كلمة المرور" : "إظهار كلمة المرور");
    btn.setAttribute("title", isVisible ? "إخفاء كلمة المرور" : "إظهار كلمة المرور");
    btn.innerHTML = `<i data-lucide="${isVisible ? "eye-off" : "eye"}" class="h-5 w-5"></i>`;
    if (window.lucide) lucide.createIcons();
  };

  renderIcon(false);

  btn.addEventListener("click", () => {
    const isVisible = input.type === "text";
    input.type = isVisible ? "password" : "text";
    renderIcon(!isVisible);
    input.focus();
  });
}

function wireLoginForm() {
  const form = document.getElementById("loginForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideToast();

    const userId = document.getElementById("userId");
    const password = document.getElementById("password");
    const role = document.getElementById("role");

    const userIdVal = (userId?.value || "").trim();
    const passwordVal = (password?.value || "").trim();
    const roleVal = role?.value || "student";

    const userIdErr = userIdVal.length === 0;
    const passwordErr = passwordVal.length === 0;
    setFieldError("userId", userIdErr);
    setFieldError("password", passwordErr);

    if (userIdErr || passwordErr) return;

    const roleLabel =
      roleVal === "student" ? "طالب" : roleVal === "supervisor" ? "مشرف" : "منسق / إدارة القسم";
    showToast(`جاري تسجيل الدخول... (${roleLabel})`);

    const apiRole =
      roleVal === "coordinator" ? "Admin" : roleVal === "supervisor" ? "Supervisor" : "Student";

    const payload = { password: passwordVal, role: apiRole };

    const allDigits = /^\d+$/.test(userIdVal);
    const numVal = Number(userIdVal);

    if (allDigits && userIdVal.length === 4) payload.display_id = userIdVal;
    else if (allDigits && userIdVal.length === 5) payload.display_id = userIdVal;
    else if (allDigits && !Number.isNaN(numVal))
      payload.user_id = numVal;
    else payload.display_id = userIdVal;

    try {
      const resp = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "Login failed" }));
        showToast(`فشل تسجيل الدخول: ${err.detail || "تحقق من البيانات"}`);
        return;
      }

      const data = await resp.json();
      setSession({
        role: roleVal,
        userId: data.user_id,
        displayId: data.display_id || userIdVal || "",
        fullName: data.full_name || "",
        accessToken: data.access_token,
        mustChangePassword: !!data.must_change_password,
        isTeamLeader: !!data.is_team_leader,
        isTeamMember: !!data.is_team_member,
        isGroupLeaderAccount: !!data.is_group_leader_account,
        teamName: data.team_name || null,
        teamMembers: Array.isArray(data.team_members) ? data.team_members : [],
        at: Date.now(),
      });

      if (data.must_change_password) {
        window.location.href = gpmsChangePasswordUrl();
      } else {
        let target = data.redirect_url || getDefaultDashboardUrl(roleVal);
        if (typeof window.gpmsHref === "function" && String(target).startsWith("/")) {
          target = window.gpmsHref(target);
        }
        window.location.href = target;
      }
    } catch {
      showToast("تعذر الاتصال بالخادم.");
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  const savedLang = localStorage.getItem("gpms_lang_v1");
  if (window.GPMS_I18N?.setLang && savedLang) {
    window.GPMS_I18N.setLang(savedLang === "en" ? "en" : "ar");
  }
  if (window.GPMS_I18N?.wireLoginLanguage) {
    window.GPMS_I18N.wireLoginLanguage();
  }
  if (window.GPMS_I18N?.wireGlobalLanguageSwitcher) {
    window.GPMS_I18N.wireGlobalLanguageSwitcher();
  }
  if (window.GPMS_I18N?.applyAllTranslations) {
    await window.GPMS_I18N.applyAllTranslations();
  } else if (window.GPMS_I18N?.applyPageTranslations) {
    window.GPMS_I18N.applyPageTranslations();
  }

  const s = getSession();
  if (s?.role === "student") {
    await refreshStudentTeamAccess();
  }
  guardRoutes();
  wireRoleScopedNavLinks();
  wireStudentTeamNav();
  wireGpmsAuthenticatedDownloads();
  if (window.lucide) lucide.createIcons();
  wirePasswordToggle();
  wireLoginForm();
  wireSidebar();
  wireActiveNav();
  wireChatbot();
  wireReferenceLibrary();
});

function wireSidebar() {
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("sidebarToggle");
  const overlay = document.getElementById("sidebarOverlay");
  if (!sidebar || !toggle || !overlay) return;

  sidebar.classList.add("gpms-sidebar");

  const isMobile = () => window.matchMedia("(max-width: 1023px)").matches;

  const syncSidebarClosedState = () => {
    if (!isMobile()) {
      sidebar.classList.remove("gpms-sidebar-closed", "translate-x-full", "gpms-sidebar-open");
      return;
    }
    if (!sidebar.classList.contains("gpms-sidebar-open")) {
      sidebar.classList.add("gpms-sidebar-closed");
    }
  };

  const open = () => {
    sidebar.classList.remove("gpms-sidebar-closed", "translate-x-full");
    sidebar.classList.add("gpms-sidebar-open");
    overlay.classList.remove("hidden");
  };

  const close = () => {
    sidebar.classList.remove("gpms-sidebar-open");
    if (isMobile()) sidebar.classList.add("gpms-sidebar-closed");
    overlay.classList.add("hidden");
  };

  syncSidebarClosedState();
  window.addEventListener("resize", syncSidebarClosedState);
  document.addEventListener("gpms:langchange", syncSidebarClosedState);

  toggle.addEventListener("click", () => {
    const isClosed =
      sidebar.classList.contains("gpms-sidebar-closed") ||
      sidebar.classList.contains("translate-x-full");
    if (isClosed) open();
    else close();
  });

  overlay.addEventListener("click", close);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
}

function wireActiveNav() {
  const links = Array.from(document.querySelectorAll("a.gpms-nav-item[href]"));
  if (links.length === 0) return;

  const current = (window.location.pathname.split("/").pop() || "").toLowerCase();
  links.forEach((a) => {
    const href = (a.getAttribute("href") || "").toLowerCase();
    if (!href || href.startsWith("#") || href.startsWith("http")) return;
    const target = href.split("/").pop();
    if (target && target === current) a.classList.add("is-active");
    else a.classList.remove("is-active");
  });
}

function wireChatbot() {
  const form = document.getElementById("chatbotForm");
  const input = document.getElementById("chatbotInput");
  const list = document.getElementById("chatbotThread");
  if (!form || !input || !list) return;

  const tr = (k, fb) => (window.GPMS_I18N?.t ? window.GPMS_I18N.t(k) : fb);
  const chatLang = () => (localStorage.getItem("gpms_lang_v1") === "en" ? "en" : "ar");

  const append = (who, text, opts = {}) => {
    const row = document.createElement("div");
    row.className = `flex ${who === "me" ? "justify-end" : "justify-start"}`;

    const bubble = document.createElement("div");
    bubble.className =
      "gpms-chat-bubble " + (who === "me" ? "gpms-chat-bubble--me" : "gpms-chat-bubble--other");
    if (opts.typing) {
      bubble.classList.add("gpms-chat-typing");
      bubble.innerHTML = '<span></span><span></span><span></span>';
    } else {
      bubble.style.whiteSpace = "pre-wrap";
      bubble.textContent = text;
    }

    row.appendChild(bubble);
    list.appendChild(row);
    list.scrollTop = list.scrollHeight;
    return row;
  };

  const removeRow = (row) => {
    if (row?.parentNode) row.parentNode.removeChild(row);
  };

  const sendQuestion = (text) => {
    const v = (text || "").trim();
    if (!v) return;
    append("me", v);
    const typingRow = append("bot", "", { typing: true });
    const s = getSession();
    fetch(`${API_BASE_URL}/chatbot/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${s?.accessToken || ""}`,
      },
      body: JSON.stringify({ message: v, lang: chatLang() }),
    })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => {
        removeRow(typingRow);
        append("bot", data.reply || tr("loadFailed", "تعذر الحصول على إجابة."));
      })
      .catch(() => {
        removeRow(typingRow);
        append(
          "bot",
          tr(
            "chatbotOffline",
            "تعذر الوصول للمساعد. تأكد من تشغيل الباك اند وتسجيل الدخول."
          )
        );
      });
  };

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const v = (input.value || "").trim();
    if (!v) return;
    input.value = "";
    sendQuestion(v);
  });

  document.querySelectorAll("[data-chatbot-suggest]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const q = btn.getAttribute("data-chatbot-suggest") || btn.textContent.trim();
      sendQuestion(q);
    });
  });

  const welcome = list.querySelector(".gpms-chat-bubble--other");
  if (welcome && window.GPMS_I18N?.t) {
    welcome.style.whiteSpace = "pre-wrap";
    welcome.textContent = tr("chatbotWelcome", welcome.textContent);
  }
}

function wireReferenceLibrary() {
  // صفحة مكتبة المراجع تستخدم bundle وخطة اعتماد كاملة في reference_library.html
  if (document.body?.dataset?.refStandalone === "true") return;

  const cards = document.getElementById("referenceCards");
  const tableBody = document.getElementById("referenceTableBody");
  if (!cards || !tableBody) return;

  const session = getSession();
  if (!session?.accessToken) return;

  fetch(`${API_BASE_URL}/references`, {
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
    },
  })
    .then((r) => (r.ok ? r.json() : Promise.reject()))
    .then((items) => {
      if (!Array.isArray(items) || items.length === 0) return;

      cards.innerHTML = "";
      tableBody.innerHTML = "";

      const top = items.slice(0, 6);
      top.forEach((p) => {
        const card = document.createElement("article");
        card.className = "rounded-2xl border border-slate-200 bg-white p-5 shadow-soft";
        card.innerHTML = `
          <div class="flex items-start justify-between gap-3">
            <div>
              <h3 class="text-sm font-extrabold text-slate-900">${escapeHtml(p.title)}</h3>
              <p class="mt-1 text-xs text-slate-500">${String(p.status)} • Project #${p.project_id}</p>
            </div>
            <span class="gpms-badge gpms-badge--approved">مرجعي</span>
          </div>
          <p class="mt-3 text-sm text-slate-600">${escapeHtml((p.description || "").slice(0, 100))}</p>
        `;
        cards.appendChild(card);
      });

      items.forEach((p) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td class="font-extrabold text-slate-900">${escapeHtml(p.title)}</td>
          <td>-</td>
          <td>-</td>
          <td>${p.supervisor_id ?? "-"}</td>
          <td>-</td>
          <td class="text-slate-600">${escapeHtml(String(p.status))}</td>
          <td><button class="gpms-pill"><span>عرض</span></button></td>
        `;
        tableBody.appendChild(tr);
      });
    })
    .catch(() => {
      // Keep static demo data if API is unavailable.
    });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

/** استخراج اسم الملف من رأس Content-Disposition (يفيد مع FileResponse من الباك اند). */
function gpmsFilenameFromContentDisposition(cd) {
  if (!cd || typeof cd !== "string") return null;
  const star = cd.match(/filename\*=(?:UTF-8'')?([^;\n]+)/i);
  if (star) {
    try {
      return decodeURIComponent(star[1].trim().replace(/^["']|["']$/g, ""));
    } catch {
      /* ignore */
    }
  }
  const quoted = cd.match(/filename="([^"]+)"/i);
  if (quoted) return quoted[1].trim();
  const plain = cd.match(/filename=([^;\s]+)/i);
  return plain ? plain[1].trim().replace(/^["']|["']$/g, "") : null;
}

function gpmsFallbackNameFromDownloadUrl(downloadUrl) {
  try {
    const u = new URL(downloadUrl);
    const seg = u.pathname.split("/").pop();
    return decodeURIComponent(seg || "") || "download";
  } catch {
    return "download";
  }
}

async function gpmsAuthenticatedDownloadFetch(downloadUrl) {
  const s = getSession();
  if (!s?.accessToken) {
    window.location.href = gpmsLoginUrl();
    throw new Error("انتهت الجلسة أو غير مصرح.");
  }
  const r = await fetch(downloadUrl, {
    headers: { Authorization: `Bearer ${s.accessToken}` },
  });
  if (!r.ok) {
    let msg = "تعذر الوصول للملف";
    try {
      const j = await r.json();
      if (typeof j.detail === "string") msg = j.detail;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  return r;
}

/**
 * أزرار تحميل/عرض للملفات المحمية بـ JWT.
 * استخدم: data-gpms-auth-download="URL كامل"
 * واختياري: data-gpms-auth-open-tab — فتح في تاب جديد بدل التحميل المباشر
 * واختياري: data-gpms-auth-filename — اسم احتياطي إن لم يُرسل Content-Disposition
 */
function wireGpmsAuthenticatedDownloads() {
  document.body.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-gpms-auth-download]");
    if (!btn) return;
    e.preventDefault();
    const url = btn.getAttribute("data-gpms-auth-download");
    if (!url) return;

    const openTab = btn.hasAttribute("data-gpms-auth-open-tab");
    const prevDisabled = btn.disabled;
    btn.disabled = true;

    try {
      const res = await gpmsAuthenticatedDownloadFetch(url);
      const blob = await res.blob();
      const fromHeader = gpmsFilenameFromContentDisposition(res.headers.get("Content-Disposition"));
      const filename =
        fromHeader ||
        btn.getAttribute("data-gpms-auth-filename") ||
        gpmsFallbackNameFromDownloadUrl(url);

      const objectUrl = URL.createObjectURL(blob);
      if (openTab) {
        window.open(objectUrl, "_blank", "noopener,noreferrer");
        window.setTimeout(() => URL.revokeObjectURL(objectUrl), 120_000);
      } else {
        const a = document.createElement("a");
        a.href = objectUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(objectUrl);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : String(err));
    } finally {
      btn.disabled = prevDisabled;
    }
  });
}

