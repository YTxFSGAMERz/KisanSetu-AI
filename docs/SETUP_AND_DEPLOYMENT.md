# KisanSetu AI — Setup & Deployment Guide

This guide covers local development, Docker Compose containerized deployment, and Supabase Cloud deployment.

---

## 1. Prerequisites

* **Node.js**: v18.0.0+ (v22+ recommended)
* **Python**: v3.11+ (v3.13 tested)
* **Docker & Docker Compose** (optional for containerized deployment)
* **Supabase CLI** (optional for cloud database management)

---

## 2. Quickstart: Local Development

### Step 1: Clone & Configure Environment
```powershell
git clone https://github.com/YourOrg/KisanSetu-AI.git
cd KisanSetu-AI

# Create your local .env
Copy-Item .env.example .env
```

### Step 2: Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Populate real Indian Mandis and CACP MSP crops
python -m app.database.setup_real_db

# Run FastAPI server (Port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Frontend Setup
In a new terminal:
```powershell
cd frontend
npm install

# Run Next.js 16 development server (Port 3000)
npm run dev
```

* **Frontend**: `http://localhost:3000`
* **Backend API**: `http://localhost:8000`
* **Swagger API Docs**: `http://localhost:8000/docs`

---

## 3. Docker Compose (Full Stack Containerized)

Start PostgreSQL, FastAPI Backend, and Next.js Frontend with a single command:

```powershell
# Copy environment configuration
Copy-Item .env.example .env

# Build and start containers
docker-compose up --build
```

To stop containers:
```powershell
docker-compose down
```

---

## 4. Supabase Cloud Database Deployment

KisanSetu AI is pre-configured with official Supabase CLI migrations:

```powershell
# 1. Authenticate with Supabase CLI
supabase login

# 2. Link your remote Supabase project
supabase link --project-ref your_project_ref

# 3. Push schema, RLS policies & real seed data
supabase db push --include-seed

# 4. In your .env, point DATABASE_URL to your Supabase PostgreSQL instance:
# DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

---

## 5. Production Environment Variables Reference

| Variable | Description | Default / Example |
|---|---|---|
| `ENVIRONMENT` | Deployment environment | `production` |
| `DEBUG` | Enable debug mode (disable in prod) | `false` |
| `DATABASE_URL` | PostgreSQL or SQLite connection URI | `postgresql+asyncpg://...` |
| `SECRET_KEY` | 32+ character JWT signing key | `openssl rand -hex 32` |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowed domains | `https://kisansetu.gov.in` |
| `DEMO_MODE` | Enable server-side one-click demo auth | `false` (in prod) |
| `SMS_PROVIDER` | SMS Provider (`SIMULATED`, `TWILIO`, `MSG91`) | `SIMULATED` |
| `SMS_API_KEY` | SMS gateway API key | `<YOUR_SMS_API_KEY>` |
| `DATA_GOV_IN_API_KEY` | Open Government Data Agmarknet key | `<YOUR_OGD_KEY>` |
| `NEXT_PUBLIC_API_URL` | Backend URL for Next.js client | `https://api.kisansetu.gov.in` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL for Next.js client | `wss://api.kisansetu.gov.in` |

---

## 6. Running Automated Tests

```powershell
cd backend
python -m pytest tests/ -v
# 13 tests checking wait-time prediction, congestion score, and slot optimization
```
