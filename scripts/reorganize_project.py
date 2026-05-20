# -*- coding: utf-8 -*-
"""One-time reorganize GPMS frontend into public/ layout."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
DATABASE = ROOT / "database"

PAGE_MAP = {
    "admin_dashboard.html": "pages/admin/admin_dashboard.html",
    "admin_users_management.html": "pages/admin/admin_users_management.html",
    "admin_assignments.html": "pages/admin/admin_assignments.html",
    "admin_approve_grades.html": "pages/admin/admin_approve_grades.html",
    "admin_system_reports.html": "pages/admin/admin_system_reports.html",
    "student_dashboard.html": "pages/student/student_dashboard.html",
    "student_project_registration.html": "pages/student/student_project_registration.html",
    "student_submit_reports.html": "pages/student/student_submit_reports.html",
    "student_notifications.html": "pages/student/student_notifications.html",
    "student_final_grade.html": "pages/student/student_final_grade.html",
    "student_contact_supervisor.html": "pages/student/student_contact_supervisor.html",
    "supervisor_dashboard.html": "pages/supervisor/supervisor_dashboard.html",
    "supervisor_review_reports.html": "pages/supervisor/supervisor_review_reports.html",
    "supervisor_proposed_projects.html": "pages/supervisor/supervisor_proposed_projects.html",
    "supervisor_enter_grades.html": "pages/supervisor/supervisor_enter_grades.html",
    "supervisor_student_notifications.html": "pages/supervisor/supervisor_student_notifications.html",
    "community.html": "pages/shared/community.html",
    "chatbot.html": "pages/shared/chatbot.html",
    "reference_library.html": "pages/shared/reference_library.html",
    "change_password.html": "pages/shared/change_password.html",
}

HTML_ROOT_FILES = list(PAGE_MAP.keys()) + ["GPMS.html", "index.html"]
ASSET_MOVES = [
    ("GPMS.css", "css/GPMS.css"),
    ("GPMS.js", "js/GPMS.js"),
    ("gpms-i18n.js", "js/gpms-i18n.js"),
    ("gpms-i18n-extra.js", "js/gpms-i18n-extra.js"),
    ("assets/uhb-logo.png", "assets/images/uhb-logo.png"),
]


def ensure_dirs():
    for sub in [
        "css",
        "js",
        "assets/images",
        "pages/admin",
        "pages/student",
        "pages/supervisor",
        "pages/shared",
    ]:
        (PUBLIC / sub).mkdir(parents=True, exist_ok=True)
    DATABASE.mkdir(parents=True, exist_ok=True)


def move_files():
    for name, dest in PAGE_MAP.items():
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, PUBLIC / dest)

    if (ROOT / "GPMS.html").is_file():
        shutil.copy2(ROOT / "GPMS.html", PUBLIC / "GPMS.html")
    if (ROOT / "index.html").is_file():
        shutil.copy2(ROOT / "index.html", PUBLIC / "index.html")

    for src, dest in ASSET_MOVES:
        s = ROOT / src
        if s.is_file():
            shutil.copy2(s, PUBLIC / dest)

    if (ROOT / "GPMS.sql").is_file():
        shutil.copy2(ROOT / "GPMS.sql", DATABASE / "GPMS.sql")
    sql_backend = ROOT / "backend" / "sql" / "schema.sql"
    if sql_backend.is_file():
        shutil.copy2(sql_backend, DATABASE / "schema.sql")

    cfg_src = ROOT / "public" / "js" / "gpms-config.js"
    if not cfg_src.is_file():
        pass  # created separately


def href_to_absolute(content: str) -> str:
  # longest filenames first
    for old in sorted(PAGE_MAP.keys(), key=len, reverse=True):
        new = "/" + PAGE_MAP[old].replace("\\", "/")
        content = content.replace(f'href="./{old}"', f'href="{new}"')
        content = content.replace(f"href='./{old}'", f'href="{new}"')
        content = re.sub(
            rf'onclick="location\.href=\'\./{re.escape(old)}\'"',
            f'onclick="location.href=\'{new}\'"',
            content,
        )
        content = re.sub(
            rf'onclick="location\.href=\'\./{re.escape(old)}\'"',
            f"onclick=\"location.href='{new}'\"",
            content,
        )

    content = content.replace('href="./GPMS.html#logout"', 'href="/GPMS.html#logout"')
    content = content.replace("href='./GPMS.html#logout'", "href='/GPMS.html#logout'")
    content = content.replace('href="./GPMS.html"', 'href="/GPMS.html"')
    content = content.replace("href='./GPMS.html'", "href='/GPMS.html'")

    content = content.replace('href="./GPMS.css"', 'href="/css/GPMS.css"')
    content = content.replace('src="./GPMS.css"', 'src="/css/GPMS.css"')

    content = content.replace('src="./gpms-i18n.js"', 'src="/js/gpms-i18n.js"')
    content = content.replace('src="./gpms-i18n-extra.js"', 'src="/js/gpms-i18n-extra.js"')
    content = content.replace('src="./GPMS.js"', 'src="/js/GPMS.js"')
    content = content.replace('src="./gpms-config.js"', 'src="/js/gpms-config.js"')

    content = content.replace('src="./assets/uhb-logo.png"', 'src="/assets/images/uhb-logo.png"')

    return content


def inject_base_and_config(html: str) -> str:
    if "<base " not in html:
        html = html.replace(
            "<head>",
            '<head>\n    <base href="/" />',
            1,
        )
    if "gpms-config.js" not in html and "GPMS.js" in html:
        html = html.replace(
            '<script src="/js/gpms-i18n-extra.js"></script>',
            '<script src="/js/gpms-i18n-extra.js"></script>\n    <script src="/js/gpms-config.js"></script>',
        )
        if "gpms-config.js" not in html:
            html = html.replace(
                '<script src="/js/GPMS.js"></script>',
                '<script src="/js/gpms-config.js"></script>\n    <script src="/js/GPMS.js"></script>',
            )
    return html


def patch_index(html: str) -> str:
    html = html.replace('url=./GPMS.html', 'url=/GPMS.html')
    html = html.replace('href="./GPMS.html"', 'href="/GPMS.html"')
    return html


def process_html_files():
    for path in PUBLIC.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        text = href_to_absolute(text)
        text = inject_base_and_config(text)
        if path.name == "index.html":
            text = patch_index(text)
        path.write_text(text, encoding="utf-8", newline="\n")


def main():
    ensure_dirs()
    move_files()
    process_html_files()
    print("Reorganization complete under:", PUBLIC)


if __name__ == "__main__":
    main()
