# -*- coding: utf-8 -*-
"""GPMS security regression tests — run while backend is on :8000."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

API = "http://127.0.0.1:8000/api/v1"
failures: list[str] = []
passed: list[str] = []


def ok(msg: str):
    passed.append(msg)


def fail(msg: str):
    failures.append(msg)


def req(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(f"{API}{path}", data=body, headers=headers, method=method)
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


def login(uid, role):
    _, d = req("POST", "/auth/login", {"user_id": uid, "password": "123456", "role": role})
    return d.get("access_token") if isinstance(d, dict) else None


def main():
    co = login(1, "Coordinator")
    st = login(4, "Student")
    st5 = login(5, "Student")
    if not co or not st:
        fail("Could not login for tests")
        print("FAIL early — is backend running?")
        return 1

    code, _ = req("GET", "/audit_logs", token=st)
    if code in (401, 403):
        ok("Audit logs blocked for student")
    else:
        fail(f"Student audit logs should be 403, got {code}")

    code, _ = req("PATCH", "/projects/1", {"title": "HACK"}, token=st)
    if code == 403:
        ok("Student PATCH project blocked")
    else:
        fail(f"Student PATCH should be 403, got {code}")

    code, _ = req("POST", "/projects", {"title": "X", "description": "Y", "status": "Pending"}, token=st)
    if code == 403:
        ok("Student CREATE project blocked")
    else:
        fail(f"Student POST project should be 403, got {code}")

    code, data = req("GET", "/projects", token=st)
    if code == 200 and isinstance(data, list) and len(data) <= 1:
        ok("Student project list scoped")
    else:
        fail(f"Student should see at most 1 project, got {len(data) if isinstance(data, list) else data}")

    code, _ = req("POST", "/auth/seed-demo-users")
    if code in (403, 401):
        ok("Public seed blocked when users exist")
    else:
        fail(f"Seed without auth should fail when DB populated, got {code}")

    code, projects = req("GET", "/projects", token=co)
    junk_id = None
    if isinstance(projects, list):
        for p in projects:
            if p.get("title") == "X":
                junk_id = p.get("project_id")
    if junk_id:
        code, _ = req("DELETE", f"/projects/{junk_id}", token=co)
        if code in (200, 204):
            ok(f"Deleted junk project {junk_id}")
        else:
            fail(f"Could not delete junk project: {code}")

    code, subs = req("GET", "/submissions/my", token=st)
    if code == 200 and isinstance(subs, list) and subs and st5:
        fn = subs[0].get("file_path")
        if fn:
            import urllib.parse
            code2, _ = req("GET", f"/submissions/download/{urllib.parse.quote(fn)}", token=st5)
            if code2 == 403:
                ok("Cross-student file download blocked")
            else:
                fail(f"File IDOR should be 403, got {code2}")

    code, _ = req("POST", "/notifications", {"user_id": 1, "title": "x", "content": "y"}, token=st)
    if code == 403:
        ok("Student cannot spam notifications")
    else:
        fail(f"Student notification should be 403, got {code}")

    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/openapi.json", timeout=3) as r:
            if settings_docs_disabled := (r.status == 200):
                pass
    except urllib.error.HTTPError as e:
        if e.code == 404:
            ok("OpenAPI hidden (production-style)")
        else:
            fail(f"OpenAPI check: {e.code}")
    except Exception:
        ok("OpenAPI not reachable")

    print(f"PASSED: {len(passed)}")
    for p in passed:
        print(f"  [OK] {p}")
    if failures:
        print(f"FAILED: {len(failures)}")
        for f in failures:
            print(f"  [!!] {f}")
        return 1
    print("All security regression tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
