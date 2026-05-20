/**
 * يضمن تطبيق الترجمة على الصفحات الداخلية بعد تحميل DOM وعند تغيير اللغة.
 */
(function () {
  function syncLangFromStorage() {
    const saved = localStorage.getItem("gpms_lang_v1");
    if (window.GPMS_I18N?.setLang) {
      window.GPMS_I18N.setLang(saved === "en" ? "en" : "ar");
    }
  }

  function applyNow() {
    syncLangFromStorage();
    if (window.GPMS_I18N?.applyPageTranslations) {
      window.GPMS_I18N.applyPageTranslations();
    }
  }

  async function applyFull() {
    syncLangFromStorage();
    if (window.GPMS_I18N?.applyAllTranslations) {
      await window.GPMS_I18N.applyAllTranslations();
    } else {
      applyNow();
    }
  }

  function onLangChange() {
    applyNow();
  }

  function init() {
    if (!document.body?.dataset?.page) return;
    applyNow();
    document.addEventListener("gpms:langchange", onLangChange);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.gpmsApplyPageI18n = applyNow;
  window.gpmsApplyPageI18nFull = applyFull;
})();
