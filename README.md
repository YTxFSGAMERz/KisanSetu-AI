# 🌾 KisanSetu AI — Smart Procurement Management Platform

> **Smart India Hackathon 2026 — Problem Statement 26032**  
> **Organization:** Ministry of Consumer Affairs, Food & Public Distribution  
> **Department:** Department of Consumer Affairs (DoCA)  
> **Theme:** Smart Automation  
> **🌐 Live Production Web App:** [https://kisansetu-sih.vercel.app](https://kisansetu-sih.vercel.app) *(Mirror: [https://kisansetu-india.vercel.app](https://kisansetu-india.vercel.app))*

---

## 🎯 Problem Statement

Farmers face **long waiting times, lack of information** regarding procurement schedules, and **uncertainty** about procurement status at Government procurement centres (Mandis).

## ✅ Solution

**KisanSetu AI** is a full-stack digital platform that enables:

| Feature | Description |
|---|---|
| 📅 **Slot Booking** | Farmers book procurement slots from home via mobile |
| 🤖 **AI Recommendations** | Smart engine ranks slots by wait time & congestion |
| 🎫 **Digital Tokens** | Unique queue tokens (A001, A042…) assigned on booking |
| 📡 **Real-Time Queue** | Live WebSocket updates — no manual refresh needed |
| ⚖️ **Digital Procurement** | Officer grades crop digitally, receipt auto-generated |
| 💰 **Payment Tracking** | Farmer tracks MSP payment from PENDING → COMPLETED |
| 🔔 **Notifications** | In-app + simulated SMS for every status change |
| 📊 **Analytics Dashboard** | Centre-wise congestion, daily volume, payment rates |

---

## 🏗️ Architecture

```
frontend/          Next.js 16 (TypeScript, Tailwind CSS, App Router)
backend/           FastAPI (Python 3.13, SQLAlchemy 2.0 async)
  ├── app/core/    Config, JWT auth, WebSocket manager
  ├── app/models/  SQLAlchemy ORM models (11 tables)
  ├── app/schemas/ Pydantic v2 request/response schemas
  ├── app/api/     REST + WebSocket routes (10 routers)
  ├── app/services/Smart engine, queue state machine, notifications
  └── app/database/Async SQLite (dev) / PostgreSQL (prod) + seed
docker-compose.yml PostgreSQL + Backend + Frontend
```

---

## 🚀 Quick Start (Local Dev — No Docker Needed)

### Backend

```powershell
cd backend

# Install dependencies
python -m pip install -r requirements.txt

# Seed local SQLite database (15 Mandis, 19 crops, 1200+ slots, demo accounts)
python -m app.database.setup_local_db

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: **http://localhost:8000/docs**

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

App available at: **http://localhost:3000**

---

## 🎬 Role Portals (Zero-Credential Server-Side Auth)

| Role | Description | Portal Route | Demo URL |
|---|---|---|---|
| 👨‍🌾 **Farmer** | Book slots, view live queue tokens, MSP tracking | `/farmer` | `/login?demo=farmer` |
| 🏛️ **Officer** | Queue call desk, digital grading, instant receipts | `/officer` | `/login?demo=officer` |
| 📊 **Gov Admin** | National procurement KPIs, congestion meters | `/admin` | `/login?demo=admin` |

> **Security Note**: In demo mode (`DEMO_MODE=true` in `.env`), portal access uses server-side JWT generation with zero passwords exposed in client bundles or network requests. In production, regular JWT email/password authentication or OTP login is enforced with credentials configured exclusively in `.env`.

---

## 🐳 Docker Compose (Full Stack)

```powershell
# Copy env template
Copy-Item .env.example .env

# Start all services (PostgreSQL + Backend + Frontend)
docker-compose up --build

# Access
# Frontend:  http://localhost:3000
# API:       http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

---

## ⚡ Supabase CLI Integration

KisanSetu AI is pre-configured for the **Supabase CLI** (`supabase/` folder with migrations and real seed data):

```powershell
# 1. Login to Supabase CLI
supabase login

# 2. Link your remote Supabase project
supabase link --project-ref your_project_ref_here

# 3. Push real schema & indexes to your Supabase project
supabase db push

# 4. (Optional) Run Supabase locally with Docker
supabase start
supabase db reset   # Applies migration + seeds real Mandis & MSP crops
```

---

## 📡 API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | JWT login |
| POST | `/api/v1/auth/register` | Farmer registration |
| GET | `/api/v1/slots/recommendations` | 🤖 AI slot ranking |
| POST | `/api/v1/bookings` | Create booking + token |
| GET | `/api/v1/queue/status` | Live queue state |
| POST | `/api/v1/queue/call-next` | Officer calls next farmer |
| POST | `/api/v1/procurements` | Create procurement record |
| POST | `/api/v1/payments/{id}/process` | Process MSP payment |
| WS | `/api/v1/ws/queue/{centre_id}` | Real-time queue events |
| WS | `/api/v1/ws/user/{user_id}` | Targeted farmer alerts |
| GET | `/api/v1/analytics/admin/dashboard` | National analytics |

---

## 🤖 Smart Recommendation Engine

Three-layer scoring algorithm:

```python
# 1. Predict wait time
wait = (queue_length × avg_processing_min × crop_complexity) / active_counters

# 2. Compute congestion score (0-100)
score = 0.4 × (booked/capacity) + 0.4 × (queue/daily_target) + 0.2 × (wait/60)

# 3. Rank slots: lower score = better slot
slot_score = 0.5 × occupancy + 0.3 × (wait/120) + 0.2 × (congestion/100)
```

Returns top-3 slots with human-readable reason and congestion label (Low / Moderate / High / Very High).

---

## 🧪 Tests

```powershell
cd backend
python -m pytest tests/ -v
# 13 tests — all passing ✅
```

---

## 📁 Project Structure

```
KisanSetu-AI/
├── backend/
│   ├── app/
│   │   ├── api/routes/         # 11 route modules
│   │   ├── core/               # config, security, WebSocket
│   │   ├── database/           # session, seed
│   │   ├── models/             # 11 ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── services/           # recommendation engine, queue, notifications
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── login/              # Auth page
│   │   ├── farmer/             # Dashboard, Book Slot, Live Queue, Payments…
│   │   ├── officer/            # Queue + Procurement Officer desk
│   │   └── admin/              # Government analytics dashboard
│   ├── context/                # Auth + WebSocket React contexts
│   ├── lib/api.ts              # Type-safe API client
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## ⚡ GitHub Actions Database Deployment (Zero Cloud Shutdown)

KisanSetu AI uses GitHub Actions as an automated database deployment engine. It completely eliminates free-tier cloud database timeouts and shutdowns (e.g. Supabase pausing due to inactivity):

- **Automatic Continuous Updates:** Whenever backend models, schemas, or seed data change on `main`, GitHub Actions automatically seeds, verifies, and packages the database.
- **Weekly Auto-Refresh:** Automatically generates fresh rolling 14-day slot schedules via cron so future slots never expire.
- **Manual 1-Click Trigger:** Go to **GitHub Actions → "Deploy & Refresh Database" → "Run workflow"** to rebuild, verify, and push the latest database snapshot.
- **Permanent Uptime:** The database snapshot is versioned in the repository (`frontend/data/seed.json`) and served by Vercel with 100% uptime, zero sleep, and zero external hosting costs.

---

## 🏆 SIH Judging Criteria

| Criterion | Implementation |
|---|---|
| **Farmer Registration & Slot Booking** | ✅ Full CRUD with OTP stub |
| **Real-Time Queue Management** | ✅ WebSocket pubsub per centre |
| **SMS/App Notifications** | ✅ In-app + simulated SMS |
| **Procurement & Payment Tracking** | ✅ End-to-end with MSP calculation |
| **Reduce Congestion & Waiting** | ✅ AI engine + congestion dashboard |

---

## 👥 Contributors & Team

| [<img src="https://github.com/YTxFSGAMERz.png" width="80px;"/><br /><sub><b>YTxFSGAMERz</b><br/>👑 Lead</sub>](https://github.com/YTxFSGAMERz) | [<img src="https://github.com/vedant-afk1999.png" width="80px;"/><br /><sub><b>vedant-afk1999</b></sub>](https://github.com/vedant-afk1999) | [<img src="https://github.com/mitanshsoliya.png" width="80px;"/><br /><sub><b>mitanshsoliya</b></sub>](https://github.com/mitanshsoliya) | [<img src="https://github.com/prachipandey2938.png" width="80px;"/><br /><sub><b>prachipandey2938</b></sub>](https://github.com/prachipandey2938) | [<img src="https://github.com/Rudradev02.png" width="80px;"/><br /><sub><b>Rudradev02</b></sub>](https://github.com/Rudradev02) | [<img src="https://github.com/patraajay402-lgtm.png" width="80px;"/><br /><sub><b>patraajay402-lgtm</b></sub>](https://github.com/patraajay402-lgtm) |
| :---: | :---: | :---: | :---: | :---: | :---: |

---

*KisanSetu AI — Empowering India's Farmers through Smart Technology*  
*Team: Smart India Hackathon 2026*
