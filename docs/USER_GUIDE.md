# KisanSetu AI — User Guide & Portal Manual

Welcome to the KisanSetu AI user guide. This document explains how farmers, procurement officers, and government administrators interact with the platform.

---

## 👨‍🌾 1. Farmer Portal (`/farmer`)

### 1.1 Dashboard
* Displays upcoming booking dates, token numbers, and live queue status.
* Quick-action buttons to book new slots, view past procurement receipts, and monitor bank transfer statuses.

### 1.2 Booking a Procurement Slot (`/farmer/book-slot`)
1. **Select Procurement Mandi**: Choose from active APMC Mandis across India.
2. **Select Commodity**: Choose your crop (e.g., Wheat, Paddy, Mustard). The current official MSP rate per quintal will be displayed automatically.
3. **Enter Quantity**: Enter the expected crop quantity in quintals.
4. **Choose AI-Recommended Slot**: 
   - The AI recommendation engine analyzes current booking occupancy and predicted wait times.
   - Recommended low-wait slots are marked with a green badge and explanation.
5. **Confirm Booking**: Receive your booking number (e.g., `BK-KNL-2026-0001`) and queue token.

### 1.3 Live Queue Tracking (`/farmer/live-queue`)
* Keep this page open on arrival at the Mandi.
* Shows:
  - Your Token Number & Queue Position.
  - Number of farmers currently ahead of you.
  - Estimated wait time in minutes.
  - Live sound & visual flash when your token is called to a counter.

### 1.4 Receipts & Payments (`/farmer/payments`)
* View official digital receipts generated after quality grading.
* Track payment status from `PENDING` → `PROCESSING` → `COMPLETED` with bank transaction reference numbers.

---

## 🏛️ 2. Procurement Officer Portal (`/officer`)

### 2.1 Counter Queue Management
1. **View Waiting Queue**: Real-time list of all arrived farmers sorted by token number.
2. **Call Next Farmer**: Click the **"Call Next Farmer"** button. This:
   - Updates the live display board.
   - Pushes real-time WebSocket alerts to the farmer's mobile screen.
   - Sends an automated SMS alert to the farmer.
3. **Mark Start**: Click **"Start Processing"** once the farmer arrives at the counter.

### 2.2 Digital Quality Grading & Receipt Issuance
1. Record weighbridge actual weight and net accepted weight.
2. Grade the produce based on Fair Average Quality (FAQ) standards (`Grade A`, `Standard`, `Below Standard`).
3. If any produce is rejected, enter the reason (e.g., *Moisture above 12% limit*).
4. Click **"Generate Receipt & Complete"**:
   - The platform calculates the payable MSP amount based on accepted weight.
   - A digitally signed receipt is generated and an automated Direct Benefit Transfer (DBT) payment request is dispatched.

---

## 📊 3. Government Admin Portal (`/admin`)

### 3.1 National Overview
* **Total Procured Volume**: Metric Tonnes of agricultural commodities purchased to date.
* **Total MSP Disbursed**: Cumulative funds transferred to farmers' bank accounts.
* **Active Beneficiaries**: Total unique farmers serviced.
* **Average Wait Time**: National average farmer wait time benchmark (in minutes).

### 3.2 Mandi Congestion & State Heatmap
* State-by-state procurement volumes and live traffic congestion meters.
* Allows policymakers to dynamically adjust daily intake quotas and redirect harvesting trucks to under-utilized mandis.
