/**
 * مبدّل اللغة + تطبيق الترجمة على كل الصفحات الداخلية
 */
(function () {
  const LANG_KEY = "gpms_lang_v1";

  function getLang() {
    return localStorage.getItem(LANG_KEY) === "en" ? "en" : "ar";
  }

  function setLang(lang) {
    localStorage.setItem(LANG_KEY, lang === "en" ? "en" : "ar");
    if (window.GPMS_I18N?.setLang) window.GPMS_I18N.setLang(lang);
  }

  async function applyLang() {
    const lang = getLang();
    if (window.GPMS_I18N?.setLang) window.GPMS_I18N.setLang(lang);
    if (window.GPMS_I18N?.applyPageTranslations) {
      window.GPMS_I18N.applyPageTranslations();
    }
    try {
      if (window.GPMS_I18N?.applyAllTranslations) {
        await window.GPMS_I18N.applyAllTranslations();
      }
    } catch (err) {
      console.error("gpms i18n apply failed:", err);
    }
    syncToggleUI();
  }

  function syncToggleUI() {
    const lang = getLang();
    document.querySelectorAll(".gpms-lang-btn").forEach((btn) => {
      btn.classList.toggle("is-active", btn.getAttribute("data-lang") === lang);
    });
    const label = document.querySelector("#gpmsLangGlobalWrap .gpms-lang-label");
    if (label) label.textContent = lang === "en" ? "Language" : "اللغة";
    const sel = document.getElementById("gpmsLangSelectGlobal");
    if (sel) sel.value = lang;
  }

  function injectLangToggle() {
    if (document.getElementById("gpmsLangGlobalWrap")) return;
    const header =
      document.querySelector("header .mx-auto.flex") ||
      document.querySelector("header [class*='mx-auto']") ||
      document.querySelector("header > div");
    if (!header) return;

    const wrap = document.createElement("div");
    wrap.id = "gpmsLangGlobalWrap";
    wrap.className = "flex shrink-0 flex-col items-end gap-1 sm:flex-row sm:items-center sm:gap-2";

    const label = document.createElement("span");
    label.className = "text-xs font-bold text-slate-600 gpms-lang-label";
    label.textContent = getLang() === "en" ? "Language" : "اللغة";

    const toggle = document.createElement("div");
    toggle.className = "gpms-lang-toggle";
    toggle.setAttribute("role", "group");

    const btnAr = document.createElement("button");
    btnAr.type = "button";
    btnAr.className = "gpms-lang-btn";
    btnAr.setAttribute("data-lang", "ar");
    btnAr.textContent = "العربية";

    const btnEn = document.createElement("button");
    btnEn.type = "button";
    btnEn.className = "gpms-lang-btn";
    btnEn.setAttribute("data-lang", "en");
    btnEn.textContent = "English";

    toggle.appendChild(btnAr);
    toggle.appendChild(btnEn);
    wrap.appendChild(label);
    wrap.appendChild(toggle);

    const sel = document.createElement("select");
    sel.id = "gpmsLangSelectGlobal";
    sel.className = "sr-only";
    sel.setAttribute("aria-hidden", "true");
    sel.tabIndex = -1;
    sel.innerHTML = '<option value="ar">ar</option><option value="en">en</option>';
    wrap.appendChild(sel);

    const badge = header.querySelector("[data-i18n-role]") || header.lastElementChild;
    if (badge) header.insertBefore(wrap, badge);
    else header.appendChild(wrap);

    [btnAr, btnEn].forEach((btn) => {
      btn.addEventListener("click", () => {
        setLang(btn.getAttribute("data-lang"));
        void applyLang();
      });
    });
    sel.addEventListener("change", (e) => {
      setLang(e.target.value);
      void applyLang();
    });
    syncToggleUI();
  }

  function init() {
    injectLangToggle();
    void applyLang();
    document.addEventListener("gpms:langchange", () => {
      syncToggleUI();
      if (window.GPMS_I18N?.applyPageTranslations) {
        window.GPMS_I18N.applyPageTranslations();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.gpmsSetLang = setLang;
  window.gpmsApplyLang = applyLang;
})();
