# KisanSetu AI — Congestion Reduction Analysis

> [!IMPORTANT]
> **SIMULATION RESULTS** — All figures are computed from a deterministic simulation.
> They are NOT derived from real operational deployment data.
> The simulation uses realistic distribution assumptions and the same queue logic
> as the KisanSetu congestion engine.

---

## Simulation Parameters

| Parameter | Value |
|---|---|
| Farmers simulated | 200 |
| Centre counters | 5 |
| Avg processing time | 20.0 min/farmer |
| Operating hours | 09:00–17:00 |
| Slot capacity | 40 farmers/slot |

---

## Results

### Baseline (No Booking System)

Farmers arrive randomly with heavy clustering in the first 2 hours (typical at
unmanaged procurement centres). First-come, first-served queuing.

| Metric | Value |
|---|---|
| **Avg Waiting Time** | **241.3 minutes** |
| Max Waiting Time | 362.0 minutes |
| Avg Queue Length | 61.0 farmers |
| Max Queue Length | 91 farmers |
| Peak Congestion Window | 11:00 |
| Farmers with Zero Wait | 2.5% |

### KisanSetu (With Intelligent Slot Booking)

Farmers distributed across time slots using capacity-aware booking.
Arrival notifications sent via SMS. 85% compliance rate assumed.

| Metric | Value |
|---|---|
| **Avg Waiting Time** | **185.1 minutes** |
| Max Waiting Time | 360.0 minutes |
| Avg Queue Length | 47.2 farmers |
| Max Queue Length | 90 farmers |
| Avg Slot Utilization | 62.5% |
| Farmers with Zero Wait | 2.5% |

---

## Estimated Impact

| Metric | Baseline | KisanSetu | **Reduction** |
|---|---|---|---|
| Avg Wait Time | 241.3 min | 185.1 min | **23.3%** |
| Max Wait Time | 362.0 min | 360.0 min | **0.6%** |
| Avg Queue Length | 61.0 | 47.2 | **22.6%** |
| Max Queue Length | 91 | 90 | **1.1%** |

---

## How KisanSetu Achieves This

```
Historical Demand (FCI data)
+ Current Bookings
+ Centre Capacity
+ Live Queue State
        ↓
Predict Congestion Per Slot (0–100 score)
        ↓
Estimate Waiting Time per Slot
        ↓
Rank Available Slots (lowest score = best)
        ↓
Recommend Lower-Congestion Slot to Farmer
        ↓
Farmer Books Recommended Slot
        ↓
SMS Notification: "Arrive by HH:MM for your slot"
        ↓
Distributed Arrivals → Shorter Physical Queue
```

---

## SIH 26032 Alignment

| Requirement | How Congestion Engine Helps |
|---|---|
| Farmer registration & slot booking | Slot recommendations prevent overbooking |
| Real-time queue management | Live congestion score per slot updates in real-time |
| SMS/app notifications | Arrival timing advice sent when congestion changes |
| Procurement & payment tracking | Reduced queue → faster processing → faster payment |
| **Reduce congestion & waiting time** | **Core objective — simulation shows 23.3% reduction** |

---

*Generated: 2026-09-04 11:41 UTC*
*KisanSetu AI — SIH Problem Statement 26032*
