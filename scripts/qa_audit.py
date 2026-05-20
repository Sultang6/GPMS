# -*- coding: utf-8 -*-
"""GPMS comprehensive QA + security smoke audit."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
API = f"{BASE}/api/v1"
PUBLIC = Path(__file__).resolve().parents[1] / "public"

findings: list[dict] = []
passed: list[str] = []


def finding(severity: str, area: str, title: str, detail: str):
    findings.append({"severity": severity, "area": area, "title": title, "detail": detail})


def ok(msg: str):
    passed.append(msg)


def req(method: str, url: str, data=None, token: str | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=8) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except Exception as e:
        return None, str(e)


def login(display_id: str, password: str, role: str):
    code, data = req("POST", f"{API}/auth/login", {
        "display_id": display_id,
        "password": password,
        "role": role,
    })
    if code != 200:
        return None, code, data
    return data.get("access_token"), code, data


def test_backend_health():
    code, data = req("GET", f"{BASE}/health")
    if code == 200 and data.get("status") == "ok":
        ok("Backend health check")
    else:
        finding("CRITICAL", "Backend", "Health endpoint failed", str(data))


def test_seed_and_logins():
    code, data = req("POST", f"{API}/auth/seed-demo-users")
    if code == 200:
        ok("Seed demo users endpoint reachable")
    else:
        finding("HIGH", "Security", "Seed endpoint error", f"HTTP {code}: {data}")

    tokens = {}
    for did, role in [("90001", "Coordinator"), ("91001", "Supervisor"), ("2584", "Student")]:
        tok, code, data = login(did, "123456", role)
        if tok:
            tokens[role] = tok
            ok(f"Login as {role} ({did})")
        else:
            finding("CRITICAL", "Auth", f"Login failed for {role}", f"HTTP {code}: {data}")
    return tokens


def test_auth_guards(tokens: dict):
    code, _ = req("GET", f"{API}/admin/stats")
    if code == 401:
        ok("Admin stats requires auth")
    else:
        finding("CRITICAL", "Auth", "Admin stats without token", f"HTTP {code}")

    st = tokens.get("Student")
    if st:
        code, _ = req("GET", f"{API}/admin/stats", token=st)
        if code == 403:
            ok("Admin stats blocked for student")
        else:
            finding("HIGH", "AuthZ", "Student can access admin stats", f"HTTP {code}")

        code, _ = req("GET", f"{API}/admin/users", token=st)
        if code == 403:
            ok("Admin users blocked for student")
        else:
            finding("HIGH", "AuthZ", "Student can list all users", f"HTTP {code}")


def test_idor(tokens: dict):
    st = tokens.get("Student")
    co = tokens.get("Coordinator")
    if not st or not co:
        return

    code, projects = req("GET", f"{API}/projects", token=st)
    if code == 200 and isinstance(projects, list) and len(projects) > 0:
        finding(
            "MEDIUM",
            "AuthZ",
            "Student sees all projects via GET /projects",
            f"Returned {len(projects)} projects — should be scoped to own team",
        )
    elif code == 200:
        ok("Student projects list empty or scoped")

    code, data = req("GET", f"{API}/audit_logs", token=st)
    if code == 200:
        finding(
            "HIGH",
            "AuthZ",
            "Any user can read audit logs",
            "GET /api/v1/audit_logs has no role check",
        )
    elif code in (403, 401):
        ok("Audit logs protected")

    code, users = req("GET", f"{API}/admin/users", token=co)
    if code == 200 and isinstance(users, list) and users:
        target = users[0]
        uid = target.get("user_id")
        code2, patched = req(
            "PATCH",
            f"{API}/projects/1",
            {"title": "QA_INJECTION_TEST"},
            token=st,
        )
        if code2 == 200:
            finding(
                "CRITICAL",
                "AuthZ",
                "Student can PATCH any project",
                f"Updated project: {patched}",
            )
        else:
            ok(f"Student blocked from PATCH project (HTTP {code2})")


def test_unauthenticated_seed():
    code, data = req("POST", f"{API}/auth/seed-demo-users")
    if code == 200:
        finding(
            "CRITICAL",
            "Security",
            "seed-demo-users is public (no auth)",
            "Anyone can call POST /auth/seed-demo-users — resets demo on empty DB",
        )


def test_api_smoke(tokens: dict):
    co = tokens.get("Coordinator")
    sup = tokens.get("Supervisor")
    st = tokens.get("Student")
    if co:
        for path in ["/admin/stats", "/projects", "/groups/teams-overview"]:
            code, data = req("GET", f"{API}{path}", token=co)
            if code == 200:
                ok(f"Coordinator GET {path}")
            else:
                finding("MEDIUM", "API", f"Coordinator failed {path}", f"HTTP {code}: {data}")
    if sup:
        code, data = req("GET", f"{API}/submissions/supervisor", token=sup)
        if code == 200:
            ok("Supervisor submissions list")
        else:
            finding("MEDIUM", "API", "Supervisor submissions failed", str(data))
    if st:
        code, data = req("GET", f"{API}/auth/me", token=st)
        if code == 200:
            ok("Student /auth/me")
        else:
            finding("MEDIUM", "API", "Student /auth/me failed", str(data))
        code, data = req(
            "POST",
            f"{API}/chatbot/ask",
            {"message": "ما حالة مشروعي؟", "lang": "ar"},
            token=st,
        )
        if code == 200 and isinstance(data, dict) and data.get("reply"):
            ok("Chatbot responds")
        else:
            finding("MEDIUM", "API", "Chatbot failed", str(data))


def test_frontend_assets():
    required_js = [
        "js/GPMS.js",
        "js/gpms-config.js",
        "js/gpms-i18n.js",
        "js/gpms-i18n-extra.js",
        "js/gpms-lang-toggle.js",
        "js/gpms-page-i18n.js",
        "css/GPMS.css",
    ]
    for rel in required_js:
        p = PUBLIC / rel.replace("/", "\\")
        if p.exists():
            ok(f"Asset exists: {rel}")
        else:
            finding("HIGH", "Frontend", f"Missing asset: {rel}", str(p))

    html_files = list(PUBLIC.rglob("*.html"))
    missing_scripts = []
    for hf in html_files:
        text = hf.read_text(encoding="utf-8")
        if "GPMS.js" in text or "gpms-i18n" in text:
            if "gpmsPublicBase" not in text and hf.name not in ("index.html",):
                if "pages" in str(hf):
                    missing_scripts.append(str(hf.relative_to(PUBLIC)))
    if missing_scripts:
        finding(
            "LOW",
            "Frontend",
            "Some pages may lack gpmsPublicBase",
            ", ".join(missing_scripts[:5]),
        )
    else:
        ok("Inner pages have asset base script")

    pages_without_toggle = []
    for hf in PUBLIC.rglob("*.html"):
        if "pages" in str(hf) and "GPMS.js" in hf.read_text(encoding="utf-8"):
            t = hf.read_text(encoding="utf-8")
            if "gpms-lang-toggle.js" not in t:
                pages_without_toggle.append(hf.name)
    if pages_without_toggle:
        finding("LOW", "i18n", "Pages missing lang toggle", ", ".join(pages_without_toggle))
    else:
        ok("All inner pages include lang toggle")


def test_config_security():
    env_example = Path(__file__).resolve().parents[1] / "backend" / ".env.example"
    if env_example.exists():
        ok(".env.example present")
    finding(
        "HIGH",
        "Security",
        "CORS allows * with credentials",
        "main.py: allow_origins=['*'] + allow_credentials=True is unsafe in production",
    )
    finding(
        "HIGH",
        "Security",
        "Default JWT secret in config",
        "config.py default jwt_secret_key='CHANGE_THIS_SECRET_KEY' — must override in .env for production",
    )
    finding(
        "MEDIUM",
        "Security",
        "Debug mode default True",
        "app_debug defaults to True — disable in production",
    )


def main():
    print("=== GPMS QA Audit ===\n")
    test_backend_health()
    tokens = test_seed_and_logins()
    if tokens:
        test_auth_guards(tokens)
        test_idor(tokens)
        test_api_smoke(tokens)
    test_unauthenticated_seed()
    test_frontend_assets()
    test_config_security()

    print(f"\nPASSED: {len(passed)}")
    for p in passed:
        print(f"  [OK] {p}")

    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings.sort(key=lambda x: sev_order.get(x["severity"], 9))

    print(f"\nFINDINGS: {len(findings)}")
    for f in findings:
        print(f"  [{f['severity']}] {f['area']}: {f['title']}")
        print(f"         {f['detail']}")

    return 1 if any(f["severity"] in ("CRITICAL", "HIGH") for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
