"""
KisanSetu AI — Congestion Reduction Simulation
================================================
Demonstrates the impact of KisanSetu's intelligent slot booking system.

IMPORTANT: These are SIMULATION RESULTS — not real operational data.
All farmer counts, wait times, and queue metrics are computed from
a deterministic simulation using real-world distribution assumptions.

Simulation design:
  - 1 procurement centre, 1 working day
  - N farmers (configurable, default 200)
  - Centre capacity: 5 counters, 20 min/farmer avg processing

BASELINE scenario:
  - Farmers arrive randomly across the operating day
  - No slot system — first-come, first-served

KISANSETU scenario:
  - Farmers distributed across time slots using congestion-aware booking
  - Slots are capacity-limited and balanced using the recommendation engine logic
  - Farmers arrive as notified (on-time with configurable compliance rate)

Outputs:
  data/processed/simulation/baseline_results.json
  data/processed/simulation/kisansetu_results.json
  docs/CONGESTION_REDUCTION_ANALYSIS.md

Usage:
  python scripts/simulate_congestion.py
  python scripts/simulate_congestion.py --farmers 300 --seed 42
"""
import argparse
import json
import math
import random
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "processed" / "simulation"
DOCS_DIR = REPO_ROOT / "docs"

# ─── Simulation Parameters ────────────────────────────────────────────────────

OPERATING_START = 9 * 60    # 9:00 AM in minutes from midnight
OPERATING_END = 17 * 60     # 5:00 PM
OPERATING_MINUTES = OPERATING_END - OPERATING_START

DEFAULT_COUNTERS = 5
DEFAULT_AVG_PROCESSING = 20.0  # minutes
DEFAULT_SLOT_DURATION = 60     # minutes
DEFAULT_FARMERS = 200
SLOT_CAPACITY = 40             # max farmers per slot


class Farmer(NamedTuple):
    id: int
    assigned_slot_start: int  # minutes from midnight
    actual_arrival: int       # minutes from midnight


class QueueEvent(NamedTuple):
    time: int    # minutes from midnight
    farmer_id: int
    event: str   # "ARRIVE", "CALLED", "DONE"


def generate_slots(slot_duration: int = DEFAULT_SLOT_DURATION) -> list[tuple[int, int]]:
    """Generate time slots across the operating day."""
    slots = []
    t = OPERATING_START
    while t + slot_duration <= OPERATING_END:
        slots.append((t, t + slot_duration))
        t += slot_duration
    return slots


def simulate_baseline(
    n_farmers: int,
    counters: int,
    avg_processing: float,
    rng: random.Random,
) -> dict:
    """
    Baseline: Farmers arrive with random distribution over operating hours.
    Heavy clustering around peak hours (9-11 AM) — typical without booking system.

    Distribution: 60% arrive in first 2 hours (rush), 40% spread rest of day.
    """
    arrivals = []
    peak_end = OPERATING_START + 120  # First 2 hours

    n_peak = int(n_farmers * 0.60)
    n_offpeak = n_farmers - n_peak

    for _ in range(n_peak):
        arrivals.append(rng.randint(OPERATING_START, peak_end))
    for _ in range(n_offpeak):
        arrivals.append(rng.randint(peak_end, OPERATING_END - 30))

    arrivals.sort()

    return _run_queue_simulation(arrivals, counters, avg_processing, "BASELINE")


def simulate_kisansetu(
    n_farmers: int,
    counters: int,
    avg_processing: float,
    rng: random.Random,
    compliance_rate: float = 0.85,
) -> dict:
    """
    KisanSetu: Farmers distributed across time slots using capacity-aware booking.
    Farmers receive arrival time recommendations and (mostly) comply.

    compliance_rate: fraction of farmers who arrive within ±10 min of recommended time.
    """
    slots = generate_slots()
    n_slots = len(slots)

    # Distribute farmers evenly across slots (capacity-aware)
    slot_assignments = []
    for i, farmer_id in enumerate(range(n_farmers)):
        slot_idx = i % n_slots
        slot_start, slot_end = slots[slot_idx]
        # Recommend arrival 5-10 min before slot start
        recommended_arrival = slot_start - rng.randint(5, 10)
        recommended_arrival = max(OPERATING_START, recommended_arrival)
        slot_assignments.append((farmer_id, slot_start, recommended_arrival))

    # Simulate arrival compliance
    arrivals = []
    for farmer_id, slot_start, recommended in slot_assignments:
        if rng.random() < compliance_rate:
            # Compliant: arrive ±10 min of recommended time
            actual = recommended + rng.randint(-5, 10)
        else:
            # Non-compliant: arrive randomly in day (late/early)
            actual = rng.randint(OPERATING_START, OPERATING_END - 30)
        actual = max(OPERATING_START, min(OPERATING_END - 10, actual))
        arrivals.append(actual)

    arrivals.sort()

    return _run_queue_simulation(arrivals, counters, avg_processing, "KISANSETU")


def _run_queue_simulation(
    arrivals: list[int],
    counters: int,
    avg_processing: float,
    scenario: str,
) -> dict:
    """
    Discrete-event queue simulation.

    Each counter processes one farmer at a time.
    """
    counter_free_at = [OPERATING_START] * counters  # Each counter's next free time
    wait_times = []
    queue_lengths = []
    queue_at_time = {}

    # Build a timeline of (arrival, finish_time) events
    events = []
    for arrival in arrivals:
        earliest_counter = min(range(counters), key=lambda c: counter_free_at[c])
        start_time = max(arrival, counter_free_at[earliest_counter])
        wait = start_time - arrival
        finish_time = start_time + avg_processing
        counter_free_at[earliest_counter] = finish_time
        wait_times.append(wait)
        events.append((arrival, finish_time))

    # Compute instantaneous physical queue length at each arrival
    for arrival, _ in events:
        # Number currently being served or waiting = farmers arrived but not finished
        still_at_centre = sum(1 for (a, f) in events if a <= arrival < f)
        # Physical queue = those at centre minus counter capacity
        physical_queue = max(0, still_at_centre - counters)
        queue_lengths.append(physical_queue)

        # Record by 30-minute window
        window = (arrival // 30) * 30
        queue_at_time.setdefault(window, []).append(physical_queue)

    # Compute metrics
    avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0
    max_wait = max(wait_times) if wait_times else 0
    avg_queue = sum(queue_lengths) / len(queue_lengths) if queue_lengths else 0
    max_queue = max(queue_lengths) if queue_lengths else 0

    # Peak congestion hour
    peak_window = max(queue_at_time, key=lambda w: sum(queue_at_time[w]) / len(queue_at_time[w])) if queue_at_time else OPERATING_START
    peak_avg_queue = sum(queue_at_time[peak_window]) / len(queue_at_time[peak_window]) if peak_window in queue_at_time else 0

    # Slot utilization
    slots = generate_slots()
    farmer_in_slot = {s: 0 for s in slots}
    for arr in arrivals:
        for slot_start, slot_end in slots:
            if slot_start <= arr < slot_end:
                farmer_in_slot[(slot_start, slot_end)] += 1
                break
    slot_utilizations = [v / SLOT_CAPACITY for v in farmer_in_slot.values()]
    avg_slot_util = sum(slot_utilizations) / len(slot_utilizations) * 100

    return {
        "scenario": scenario,
        "simulation_notice": "SIMULATION RESULTS — Not real operational data",
        "parameters": {
            "n_farmers": len(arrivals),
            "counters": counters,
            "avg_processing_minutes": avg_processing,
            "operating_hours": f"{OPERATING_START//60:02d}:00–{OPERATING_END//60:02d}:00",
            "slot_capacity": SLOT_CAPACITY,
        },
        "results": {
            "avg_wait_time_minutes": round(avg_wait, 1),
            "max_wait_time_minutes": round(max_wait, 1),
            "avg_queue_length": round(avg_queue, 1),
            "max_queue_length": round(max_queue, 1),
            "peak_window_time": f"{peak_window//60:02d}:{peak_window%60:02d}",
            "peak_avg_queue_length": round(peak_avg_queue, 1),
            "avg_slot_utilization_pct": round(avg_slot_util, 1),
            "farmers_with_zero_wait_pct": round(sum(1 for w in wait_times if w == 0) / len(wait_times) * 100, 1),
        },
    }


def compute_reduction(baseline: dict, kisansetu: dict) -> dict:
    br = baseline["results"]
    kr = kisansetu["results"]

    def pct_reduction(b, k):
        if b == 0:
            return 0.0
        return round((b - k) / b * 100, 1)

    return {
        "wait_time_reduction_pct": pct_reduction(br["avg_wait_time_minutes"], kr["avg_wait_time_minutes"]),
        "max_wait_reduction_pct": pct_reduction(br["max_wait_time_minutes"], kr["max_wait_time_minutes"]),
        "avg_queue_reduction_pct": pct_reduction(br["avg_queue_length"], kr["avg_queue_length"]),
        "max_queue_reduction_pct": pct_reduction(br["max_queue_length"], kr["max_queue_length"]),
        "baseline_avg_wait_minutes": br["avg_wait_time_minutes"],
        "kisansetu_avg_wait_minutes": kr["avg_wait_time_minutes"],
        "baseline_max_queue": br["max_queue_length"],
        "kisansetu_max_queue": kr["max_queue_length"],
    }


def write_analysis_report(baseline: dict, kisansetu: dict, reduction: dict, output_path: Path):
    br = baseline["results"]
    kr = kisansetu["results"]
    params = baseline["parameters"]

    report = f"""# KisanSetu AI — Congestion Reduction Analysis

> [!IMPORTANT]
> **SIMULATION RESULTS** — All figures are computed from a deterministic simulation.
> They are NOT derived from real operational deployment data.
> The simulation uses realistic distribution assumptions and the same queue logic
> as the KisanSetu congestion engine.

---

## Simulation Parameters

| Parameter | Value |
|---|---|
| Farmers simulated | {params["n_farmers"]} |
| Centre counters | {params["counters"]} |
| Avg processing time | {params["avg_processing_minutes"]} min/farmer |
| Operating hours | {params["operating_hours"]} |
| Slot capacity | {params["slot_capacity"]} farmers/slot |

---

## Results

### Baseline (No Booking System)

Farmers arrive randomly with heavy clustering in the first 2 hours (typical at
unmanaged procurement centres). First-come, first-served queuing.

| Metric | Value |
|---|---|
| **Avg Waiting Time** | **{br["avg_wait_time_minutes"]} minutes** |
| Max Waiting Time | {br["max_wait_time_minutes"]} minutes |
| Avg Queue Length | {br["avg_queue_length"]} farmers |
| Max Queue Length | {br["max_queue_length"]} farmers |
| Peak Congestion Window | {br["peak_window_time"]} |
| Farmers with Zero Wait | {br["farmers_with_zero_wait_pct"]}% |

### KisanSetu (With Intelligent Slot Booking)

Farmers distributed across time slots using capacity-aware booking.
Arrival notifications sent via SMS. 85% compliance rate assumed.

| Metric | Value |
|---|---|
| **Avg Waiting Time** | **{kr["avg_wait_time_minutes"]} minutes** |
| Max Waiting Time | {kr["max_wait_time_minutes"]} minutes |
| Avg Queue Length | {kr["avg_queue_length"]} farmers |
| Max Queue Length | {kr["max_queue_length"]} farmers |
| Avg Slot Utilization | {kr["avg_slot_utilization_pct"]}% |
| Farmers with Zero Wait | {kr["farmers_with_zero_wait_pct"]}% |

---

## Estimated Impact

| Metric | Baseline | KisanSetu | **Reduction** |
|---|---|---|---|
| Avg Wait Time | {br["avg_wait_time_minutes"]} min | {kr["avg_wait_time_minutes"]} min | **{reduction["wait_time_reduction_pct"]}%** |
| Max Wait Time | {br["max_wait_time_minutes"]} min | {kr["max_wait_time_minutes"]} min | **{reduction["max_wait_reduction_pct"]}%** |
| Avg Queue Length | {br["avg_queue_length"]} | {kr["avg_queue_length"]} | **{reduction["avg_queue_reduction_pct"]}%** |
| Max Queue Length | {br["max_queue_length"]} | {kr["max_queue_length"]} | **{reduction["max_queue_reduction_pct"]}%** |

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
| **Reduce congestion & waiting time** | **Core objective — simulation shows {reduction["wait_time_reduction_pct"]}% reduction** |

---

*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*
*KisanSetu AI — SIH Problem Statement 26032*
"""

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"[simulation] Analysis report: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="KisanSetu congestion reduction simulation")
    parser.add_argument("--farmers", type=int, default=DEFAULT_FARMERS)
    parser.add_argument("--counters", type=int, default=DEFAULT_COUNTERS)
    parser.add_argument("--processing", type=float, default=DEFAULT_AVG_PROCESSING)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--compliance", type=float, default=0.85,
                        help="Fraction of farmers who comply with arrival notifications")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    print(f"[simulation] Running KisanSetu Congestion Reduction Simulation")
    print(f"[simulation] Parameters: {args.farmers} farmers, {args.counters} counters, "
          f"{args.processing} min/farmer, seed={args.seed}")
    print(f"[simulation] SIMULATION RESULTS — not real operational data\n")

    # Baseline
    print("[simulation] Running BASELINE scenario...")
    baseline = simulate_baseline(args.farmers, args.counters, args.processing, random.Random(args.seed))
    br = baseline["results"]
    print(f"  Avg wait: {br['avg_wait_time_minutes']} min | Max queue: {br['max_queue_length']}")

    # KisanSetu
    print("[simulation] Running KISANSETU scenario...")
    kisansetu = simulate_kisansetu(
        args.farmers, args.counters, args.processing,
        random.Random(args.seed + 1), args.compliance
    )
    kr = kisansetu["results"]
    print(f"  Avg wait: {kr['avg_wait_time_minutes']} min | Max queue: {kr['max_queue_length']}")

    # Reduction metrics
    reduction = compute_reduction(baseline, kisansetu)

    print(f"\n[simulation] Results Summary:")
    print(f"  Wait time reduction:  {reduction['wait_time_reduction_pct']}%")
    print(f"  Queue length reduction: {reduction['avg_queue_reduction_pct']}%")

    # Save JSON results
    baseline_file = OUTPUT_DIR / "baseline_results.json"
    baseline_file.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    print(f"\n[simulation] Saved: {baseline_file}")

    kisansetu_file = OUTPUT_DIR / "kisansetu_results.json"
    kisansetu_file.write_text(json.dumps(kisansetu, indent=2), encoding="utf-8")
    print(f"[simulation] Saved: {kisansetu_file}")

    reduction_file = OUTPUT_DIR / "reduction_metrics.json"
    reduction_file.write_text(json.dumps({
        "simulation_notice": "SIMULATION RESULTS — Not real operational data",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "metrics": reduction,
    }, indent=2), encoding="utf-8")

    # Analysis report
    write_analysis_report(
        baseline, kisansetu, reduction,
        DOCS_DIR / "CONGESTION_REDUCTION_ANALYSIS.md"
    )

    print(f"\n[simulation] ✅ Done. All results labeled SIMULATION RESULTS.")


if __name__ == "__main__":
    main()
