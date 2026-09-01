# KisanSetu AI — REST API & WebSocket Specification

**Base URL**: `http://localhost:8000/api/v1` (or your production deployment domain)  
**Interactive Docs**: `http://localhost:8000/docs` (Swagger UI) / `http://localhost:8000/redoc` (ReDoc)  
**Protocol**: REST over HTTPS + WebSockets (WSS)  

---

## 1. Authentication & Identity

All secured endpoints require the `Authorization` header with a valid Bearer JWT:
```http
Authorization: Bearer <your_access_token>
```

### 1.1 Register Farmer
* **Endpoint**: `POST /auth/register`
* **Access**: Public
* **Request Body**:
```json
{
  "name": "Rajesh Verma",
  "phone": "9876543210",
  "email": "rajesh.farmer@example.com",
  "password": "SecurePassword123!",
  "role": "FARMER"
}
```
* **Response (200 OK)**:
```json
{
  "id": 1,
  "name": "Rajesh Verma",
  "phone": "9876543210",
  "email": "rajesh.farmer@example.com",
  "role": "FARMER",
  "is_active": true
}
```

### 1.2 User Login
* **Endpoint**: `POST /auth/login`
* **Access**: Public
* **Request Body**:
```json
{
  "email": "rajesh.farmer@example.com",
  "password": "SecurePassword123!"
}
```
* **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "FARMER",
  "name": "Rajesh Verma"
}
```

### 1.3 Server-Side Demo Login (Gated by `DEMO_MODE=true`)
* **Endpoint**: `POST /auth/demo-login`
* **Access**: Public (Development / Hackathon Demo only)
* **Request Body**:
```json
{
  "role": "FARMER"
}
```
* **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "FARMER",
  "name": "Demo Farmer (Rajesh Verma)"
}
```

### 1.4 Get Current User Profile
* **Endpoint**: `GET /auth/me`
* **Access**: Authenticated (`FARMER`, `PROCUREMENT_OFFICER`, `GOVERNMENT_ADMIN`)
* **Response (200 OK)**: User profile object.

---

## 2. Procurement Centres & Real Market Data

### 2.1 List APMC Procurement Centres
* **Endpoint**: `GET /centres`
* **Query Parameters**:
  - `state` (optional): Filter centres by Indian state (e.g. `Haryana`, `Punjab`, `Maharashtra`).
* **Response (200 OK)**:
```json
[
  {
    "id": 1,
    "name": "Karnal Grain Mandi — Haryana State Agricultural Marketing Board",
    "code": "APMC-HR-KNL-001",
    "address": "Model Town, Sector 12, Karnal, Haryana 132001",
    "district": "Karnal",
    "state": "Haryana",
    "latitude": 29.6857,
    "longitude": 76.9905,
    "daily_capacity": 250,
    "processing_capacity": 10,
    "avg_processing_minutes": 15.0,
    "is_active": true,
    "contact_phone": "0184-2256789"
  }
]
```

### 2.2 List Mandated MSP Crops
* **Endpoint**: `GET /centres/crops`
* **Response (200 OK)**:
```json
[
  {
    "id": 1,
    "name": "Wheat",
    "name_hi": "गेहूँ",
    "name_gu": "ઘઉં",
    "category": "cereal",
    "unit": "quintal",
    "msp_per_quintal": 2275.0,
    "processing_complexity": 1.0
  }
]
```

### 2.3 Live Agmarknet / e-NAM Market Prices
* **Endpoint**: `GET /centres/live-prices`
* **Query Parameters**:
  - `state` (optional): `Punjab`
  - `commodity` (optional): `Wheat`
* **Response (200 OK)**:
```json
[
  {
    "state": "Haryana",
    "district": "Karnal",
    "market": "Karnal",
    "commodity": "Wheat",
    "modal_price": 2275.0,
    "variety": "FAQ"
  }
]
```

---

## 3. Slot Booking & AI Recommendation Engine

### 3.1 Get AI Slot Recommendations
* **Endpoint**: `GET /slots/recommendations`
* **Query Parameters**:
  - `centre_id` (required, int): `1`
  - `target_date` (required, string): `2026-09-02`
  - `crop_id` (required, int): `1`
* **Response (200 OK)**:
```json
[
  {
    "slot_id": 1,
    "centre_id": 1,
    "slot_date": "2026-09-02",
    "start_time": "09:00:00",
    "end_time": "11:00:00",
    "capacity": 25,
    "booked_count": 2,
    "predicted_wait_minutes": 4.5,
    "congestion_score": 14.8,
    "congestion_label": "Low",
    "score": 0.08,
    "recommendation_reason": "⚡ Best choice — lowest expected wait time and smooth traffic"
  }
]
```

### 3.2 Create Slot Booking
* **Endpoint**: `POST /bookings`
* **Access**: Authenticated Farmer
* **Request Body**:
```json
{
  "centre_id": 1,
  "slot_id": 1,
  "crop_id": 1,
  "expected_quantity": 40.0,
  "notes": "Delivering via tractor HR-05-AB-1234"
}
```
* **Response (201 Created)**:
```json
{
  "id": 1,
  "booking_number": "BK-KNL-2026-0001",
  "farmer_id": 1,
  "centre_id": 1,
  "slot_id": 1,
  "crop_id": 1,
  "expected_quantity": 40.0,
  "booking_status": "CONFIRMED",
  "token_number": "A001",
  "queue_position": 1,
  "estimated_wait_minutes": 15.0,
  "created_at": "2026-09-01T12:00:00Z"
}
```

---

## 4. Real-Time Queue Management

### 4.1 Get Live Queue Status
* **Endpoint**: `GET /queue/status`
* **Query Parameters**: `centre_id=1`
* **Response (200 OK)**:
```json
{
  "centre_id": 1,
  "current_token": "A001",
  "waiting_count": 4,
  "processing_count": 1,
  "completed_today": 28,
  "no_show_count": 1,
  "avg_processing_minutes": 15.0,
  "estimated_wait_for_next": 15.0,
  "queue": [
    {
      "token_number": "A002",
      "queue_position": 2,
      "status": "WAITING",
      "farmer_name": "Suresh Patel",
      "crop_name": "Wheat",
      "expected_quantity": 30.0,
      "farmers_ahead": 1,
      "estimated_wait_minutes": 15.0
    }
  ]
}
```

### 4.2 Officer: Call Next Farmer
* **Endpoint**: `POST /queue/call-next?centre_id=1`
* **Access**: Role `PROCUREMENT_OFFICER` or `CENTRE_ADMIN`
* **Response (200 OK)**: Next `QueueToken` in sequence. Triggers WebSocket & SMS alerts.

---

## 5. Digital Procurement Grading & Payments

### 5.1 Create Procurement Record
* **Endpoint**: `POST /procurements`
* **Access**: Role `PROCUREMENT_OFFICER`
* **Request Body**:
```json
{
  "booking_id": 1,
  "crop_id": 1,
  "expected_quantity": 40.0,
  "actual_quantity": 40.0,
  "accepted_quantity": 38.5,
  "rejected_quantity": 1.5,
  "quality_grade": "GRADE_A",
  "procurement_amount": 87587.5,
  "rejection_reason": "High moisture content in 1.5 quintals"
}
```
* **Response (200 OK)**: Digital receipt generated with unique `receipt_number`.

### 5.2 Process Direct DBT Payment
* **Endpoint**: `POST /payments/{payment_id}/process`
* **Access**: Role `PROCUREMENT_OFFICER` or `GOVERNMENT_ADMIN`
* **Response (200 OK)**: Payment state changed to `COMPLETED` with bank `transaction_reference`.

---

## 6. National Analytics Dashboard

### 6.1 Government Admin Analytics
* **Endpoint**: `GET /analytics/admin/dashboard`
* **Access**: Role `GOVERNMENT_ADMIN`
* **Response (200 OK)**:
```json
{
  "total_procured_metric_tonnes": 4825.6,
  "total_msp_disbursed_inr": 109850000.0,
  "total_farmers_benefitted": 3420,
  "average_mandi_wait_time_minutes": 18.4,
  "active_procurement_centres": 12,
  "state_breakdown": [
    { "state": "Punjab", "volume_mt": 1850.0, "disbursed_cr": 4.25 },
    { "state": "Haryana", "volume_mt": 1420.0, "disbursed_cr": 3.23 }
  ]
}
```

---

## 7. Real-Time WebSockets

### 7.1 Mandi Queue Live Stream
* **URL**: `ws://localhost:8000/api/v1/ws/queue/{centre_id}`
* **Payload Events**:
```json
{
  "event": "FARMER_CALLED",
  "data": {
    "token_number": "A003",
    "counter_number": 2,
    "timestamp": "2026-09-01T12:30:00Z"
  }
}
```

### 7.2 Authenticated Private Farmer Stream
* **URL**: `ws://localhost:8000/api/v1/ws/user/{user_id}?token=<JWT_TOKEN>`
* **Authentication**: Verified via JWT query parameter. Rejects unauthorized connections with code `1008 (Policy Violation)`.
