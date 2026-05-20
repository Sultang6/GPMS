# -*- coding: utf-8 -*-
import json
import urllib.error
import urllib.request

API = "http://127.0.0.1:8000/api/v1"


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
    return d.get("access_token")


co = login(1, "Coordinator")
st = login(4, "Student")
sup = login(2, "Supervisor")

tests = []

code, data = req("GET", "/audit_logs", token=st)
tests.append(("Student audit logs", code, "403/401 expected", code in (401, 403)))

code, data = req("GET", "/projects", token=st)
tests.append(("Student list all projects", code, f"count={len(data) if isinstance(data,list) else data}", code == 200))

code, data = req("PATCH", "/projects/1", {"title": "HACKED_BY_QA"}, token=st)
tests.append(("Student PATCH project", code, data, code != 200))

code, data = req("POST", "/projects", {"title": "X", "description": "Y", "status": "Pending"}, token=st)
tests.append(("Student CREATE project", code, data, code != 201))

code, data = req("GET", "/projects/1/students", token=st)
emails = [u.get("email") for u in data] if isinstance(data, list) else data
tests.append(("Student read project students emails", code, emails, True))

code, data = req("GET", "/admin/users", token=sup)
tests.append(("Supervisor list users", code, "403 expected", code == 403))

code, data = req("GET", "/submissions", token=co)
tests.append(("Coordinator all submissions", code, f"count={len(data) if isinstance(data,list) else '?'}", code == 200))

code, data = req("GET", "/grades/student/4/project/1", token=st)
tests.append(("Student own grades", code, "ok", code == 200))

code, data = req("GET", "/grades/student/5/project/1", token=st)
tests.append(("Student other student grades IDOR", code, data, code in (403, 404)))

code, data = req("POST", "/chatbot/ask", {"message": "help", "lang": "en"}, token=st)
tests.append(("Chatbot EN", code, (data.get("reply") or "")[:60], code == 200))

# invalid token
code, data = req("GET", "/auth/me", token="invalid.token.here")
tests.append(("Invalid JWT rejected", code, data, code == 401))

# OpenAPI docs in prod concern
code, data = req("GET", "/../openapi.json".replace("/api/v1/../openapi.json", ""), token=None)
import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/openapi.json", timeout=5) as r:
        tests.append(("OpenAPI exposed", r.status, "docs public", r.status == 200))
except Exception as e:
    tests.append(("OpenAPI exposed", 0, str(e), False))

print("=== Extended Security/API Tests ===")
for name, code, detail, expected in tests:
    status = "PASS" if expected else "FAIL"
    print(f"[{status}] {name}: HTTP {code} | {detail}")
