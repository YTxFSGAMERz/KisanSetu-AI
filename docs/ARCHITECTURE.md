# KisanSetu AI — Architecture & Technical Design Document

**Project**: KisanSetu AI (किसान सेतु)  
**Problem Statement ID**: 26032 | Smart Automation  
**Ministry**: Ministry of Consumer Affairs, Food & Public Distribution  
**Department**: Department of Consumer Affairs (DoCA)  

---

## 1. System Architecture Overview

KisanSetu AI is engineered as an enterprise, event-driven, full-stack platform consisting of a high-performance Next.js 16 frontend, an asynchronous FastAPI backend, a real-time WebSocket broker, and a PostgreSQL / Supabase cloud data layer.

```mermaid
graph TB
    subgraph Client Layer ["Client Tier (Next.js 16 + Tailwind CSS v4)"]
        FARMER["👨‍🌾 Farmer Portal (/farmer)"]
        OFFICER["🏛️ Officer Counter Desk (/officer)"]
        ADMIN["📊 Government Admin Dashboard (/admin)"]
    end

    subgraph Gateway ["API Gateway & Security Layer"]
        CORS["CORS & Origin Isolation"]
        SEC_HEADERS["Security Headers Middleware (CSP, HSTS, DENY)"]
        JWT_AUTH["JWT Authentication & RBAC Engine"]
        RATE_LIMIT["Input Validation & IDOR Shield"]
    end

    subgraph Backend Layer ["Backend Services Tier (FastAPI 0.115)"]
        AUTH_SVC["Auth & Identity Service"]
        SLOT_ENGINE["🤖 AI Slot Recommendation Engine"]
        QUEUE_SVC["⚡ Dynamic Queue & Token Manager"]
        PROC_SVC["🌾 Digital FAQ Grading & MSP Calculator"]
        PAY_SVC["💳 Direct Payment & DBT Tracker"]
        AGMARK_SVC["🌐 Agmarknet / e-NAM Live Data Client"]
        WS_HUB["📡 WebSocket Event Dispatcher"]
    end

    subgraph Data Layer ["Cloud Data Tier (PostgreSQL / Supabase)"]
        SUPA_DB[("PostgreSQL 15+ / Supabase DB")]
        RLS["Row Level Security (RLS) Isolation"]
        REALTIME_PUB["Supabase Realtime WAL Engine"]
    end

    subgraph External ["External Government Gateways"]
        SMS_GW["SMS / WhatsApp Gateway"]
        DATA_GOV["Open Government Data (data.gov.in)"]
    end

    FARMER --> CORS
    OFFICER --> CORS
    ADMIN --> CORS

    CORS --> SEC_HEADERS --> JWT_AUTH --> RATE_LIMIT

    RATE_LIMIT --> AUTH_SVC
    RATE_LIMIT --> SLOT_ENGINE
    RATE_LIMIT --> QUEUE_SVC
    RATE_LIMIT --> PROC_SVC
    RATE_LIMIT --> PAY_SVC
    RATE_LIMIT --> AGMARK_SVC

    QUEUE_SVC --> WS_HUB
    WS_HUB -.-> FARMER
    WS_HUB -.-> OFFICER

    AUTH_SVC --> RLS --> SUPA_DB
    SLOT_ENGINE --> RLS --> SUPA_DB
    QUEUE_SVC --> RLS --> SUPA_DB
    PROC_SVC --> RLS --> SUPA_DB
    PAY_SVC --> RLS --> SUPA_DB

    SUPA_DB --> REALTIME_PUB
    AGMARK_SVC --> DATA_GOV
    QUEUE_SVC --> SMS_GW
```

---

## 2. Component Hierarchy & C4 Container Model

| Container | Technology Stack | Key Responsibilities |
|---|---|---|
| **Frontend Web App** | Next.js 16.3 (Turbopack), React 19, Tailwind CSS v4, Lucide Icons | Responsive multilingual portal for Farmers, Officers, and Admins; real-time queue tracker; slot booking wizard. |
| **Backend REST API** | FastAPI 0.115, Python 3.13, Pydantic v2, SQLAlchemy 2.0 Async | Business logic, JWT authentication, slot scheduling, IDOR protection, and metrics aggregation. |
| **Smart Recommendation Engine** | Pure Python Algorithmic Engine (NumPy/Math) | 3-factor congestion analysis, wait-time prediction, multi-mandi load balancing. |
| **Real-Time WebSocket Hub** | Starlette WebSockets & Supabase Realtime | Zero-polling instantaneous queue updates, counter call rings, and SMS dispatch alerts. |
| **Database & Persistence** | PostgreSQL 15+ / Supabase Cloud with RLS | Relational storage for 11 core entities, foreign key constraints, automated WAL replication. |

---

## 3. Database Entity Relationship Model (ERD)

```mermaid
erDiagram
    USERS ||--o| FARMERS : "extends"
    FARMERS ||--o{ BOOKINGS : "creates"
    PROCUREMENT_CENTRES ||--o{ SLOTS : "schedules"
    PROCUREMENT_CENTRES ||--o{ BOOKINGS : "hosts"
    SLOTS ||--o{ BOOKINGS : "allocates"
    CROPS ||--o{ BOOKINGS : "categorizes"
    BOOKINGS ||--|| QUEUE_TOKENS : "generates"
    BOOKINGS ||--o| PROCUREMENTS : "produces"
    PROCUREMENTS ||--|| PAYMENTS : "initiates"
    USERS ||--o{ NOTIFICATIONS : "receives"

    USERS {
        int id PK
        string name
        string phone UK
        string email UK
        string password_hash
        enum role
        boolean is_active
        timestamp created_at
    }

    FARMERS {
        int id PK
        int user_id FK
        string farmer_registration_number UK
        string aadhaar_last4
        string language
        string village
        string district
        string state
        float land_area_acres
        string bank_account_number
        string bank_ifsc
    }

    PROCUREMENT_CENTRES {
        int id PK
        string name
        string code UK
        text address
        string district
        string state
        float latitude
        float longitude
        int daily_capacity
        int processing_capacity
        float avg_processing_minutes
        boolean is_active
    }

    CROPS {
        int id PK
        string name UK
        string name_hi
        string name_gu
        string category
        string unit
        float msp_per_quintal
        float processing_complexity
    }

    SLOTS {
        int id PK
        int centre_id FK
        date slot_date
        time start_time
        time end_time
        int capacity
        int booked_count
        enum status
    }

    BOOKINGS {
        int id PK
        int farmer_id FK
        int centre_id FK
        int slot_id FK
        int crop_id FK
        float expected_quantity
        string booking_number UK
        enum booking_status
    }

    QUEUE_TOKENS {
        int id PK
        int booking_id FK
        int centre_id FK
        string token_number
        int queue_position
        enum status
        float estimated_wait_minutes
        timestamp arrival_time
        timestamp called_at
    }

    PROCUREMENTS {
        int id PK
        int booking_id FK
        int crop_id FK
        float actual_quantity
        float accepted_quantity
        float rejected_quantity
        enum quality_grade
        float procurement_amount
        enum status
        string receipt_number UK
    }

    PAYMENTS {
        int id PK
        int procurement_id FK
        float amount
        enum status
        string transaction_reference UK
    }

    NOTIFICATIONS {
        int id PK
        int user_id FK
        string title
        text message
        enum type
        enum channel
        boolean is_read
    }
```

---

## 4. 🤖 AI Recommendation Engine Formula

The AI Slot Recommendation Engine prevents mandi gridlock by distributing farmer arrivals across low-congestion timeslots and nearby centres:

### Formula 1: Predicted Wait Time (\(\hat{W}\))
$$\hat{W} = \frac{Q \times T_{avg} \times C_{crop}}{N_{counters}}$$

* \(Q\): Number of farmers currently waiting ahead in the physical queue.
* \(T_{avg}\): Average handling time for the centre (default: 15–20 minutes).
* \(C_{crop}\): Commodity grading complexity factor (e.g., Wheat = 1.0, Mustard = 1.2, Cotton = 1.4).
* \(N_{counters}\): Active processing counters operating at the mandi.

### Formula 2: Centre Congestion Index (\(CI \in [0, 100]\))
$$CI = \min\left(100,\; 40 \times \frac{B}{Cap_{slot}} + 40 \times \frac{Q}{Cap_{daily}} + 20 \times \frac{\hat{W}}{60}\right)$$

* \(B / Cap_{slot}\): Slot booking occupancy ratio.
* \(Q / Cap_{daily}\): Daily procurement target throughput ratio.
* \(\hat{W} / 60\): Expected waiting hour pressure.

### Formula 3: Slot Optimization Score (\(S_{slot}\))
$$S_{slot} = 0.5 \times \left(\frac{B}{Cap}\right) + 0.3 \times \min\left(1, \frac{\hat{W}}{120}\right) + 0.2 \times \left(\frac{CI}{100}\right)$$

Slots are sorted in ascending order of \(S_{slot}\). The top 3 optimal slots are tagged with human-readable recommendations (e.g., *"⚡ Fastest processing with low queue"*).

---

## 5. Real-Time Event Driven Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Farmer
    participant App as Frontend (Next.js)
    participant API as Backend (FastAPI)
    participant DB as Supabase DB
    participant WS as WebSocket Hub
    actor Officer

    Farmer->>App: Book slot for Wheat (25 Qtl)
    App->>API: POST /api/v1/bookings
    API->>DB: Insert Booking & generate Token (A014)
    API-->>App: Booking Confirmed (Token: A014)

    Farmer->>App: Arrives at Mandi & opens Live Queue
    App->>WS: Connect /ws/queue/1 & /ws/user/1?token=JWT
    
    Officer->>App: Click "Call Next Farmer"
    App->>API: POST /api/v1/queue/call-next
    API->>DB: Update Token A014 -> CALLED
    API->>WS: Broadcast FARMER_CALLED {token: A014, counter: 3}
    WS-->>App: Visual Flash + Bell Sound on Farmer App
    WS-->>Farmer: Push SMS: "Token A014 please proceed to Counter 3"

    Officer->>API: POST /api/v1/procurements (Grade A, 25 Qtl)
    API->>DB: Insert Procurement & Auto-generate Payment
    API->>WS: Broadcast PROCUREMENT_COMPLETED
    WS-->>Farmer: Alert: "Procurement approved! ₹56,875 initiated to bank account"
```
