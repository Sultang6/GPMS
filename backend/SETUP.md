# GPMS Backend Quick Setup (Windows)

## 1) Prepare Python environment

```powershell
cd "c:\Users\Abdullah\Desktop\GPMS Souers cood\backend"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2) Prepare environment variables

```powershell
Copy-Item ".env.example" ".env"
```

## 3) Start PostgreSQL + pgAdmin via Docker

```powershell
docker compose up -d
```

From `backend` folder, this uses `docker-compose.yml`.

- PostgreSQL: `localhost:5432`
- pgAdmin: `http://localhost:5050`
  - Email: `admin@gpms.local`
  - Password: `admin123`

> The SQL schema at `sql/schema.sql` is executed automatically when PostgreSQL is initialized for the first time.

## 4) Run backend API

```powershell
python run.py
```

Health check:

```powershell
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## 5) Seed demo users (first time)

```powershell
curl -X POST http://localhost:8000/api/v1/auth/seed-demo-users
```

Demo password: `123456`

## 6) Frontend login

- Open `GPMS.html`
- Use `user_id` (from DB) + password `123456`
- Role must match (`Student`, `Supervisor`, or `Admin`)

## 7) Useful commands

Stop Docker services:

```powershell
docker compose down
```

Reset DB fully (delete data volume):

```powershell
docker compose down -v
docker compose up -d
```

