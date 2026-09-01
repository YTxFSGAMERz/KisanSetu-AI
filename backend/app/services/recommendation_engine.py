"""
KisanSetu AI — Smart Recommendation Engine (Phase 6)

Deterministic algorithm for:
  1. Waiting time prediction
  2. Congestion scoring (0-100)
  3. Smart slot ranking + human-readable reasoning

Architecture is designed so an ML regression model (scikit-learn / TensorFlow)
can be swapped in as the `predict_wait_time` implementation later.
"""
import math
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.queue_token import QueueToken, TokenStatus
from app.models.slot import Slot, SlotStatus
from app.models.centre import ProcurementCentre

if TYPE_CHECKING:
    from app.models.crop import Crop


# ─── Crop Processing Complexity Factors ──────────────────────────────────────
# These represent relative difficulty of weighing, sampling, grading each crop.
# Could eventually be derived from a trained model on historical data.
DEFAULT_COMPLEXITY = 1.0

# ─── Congestion Labels ───────────────────────────────────────────────────────
def congestion_label(score: float) -> str:
    if score < 25:
        return "Low"
    elif score < 50:
        return "Moderate"
    elif score < 75:
        return "High"
    return "Very High"


def congestion_color(score: float) -> str:
    if score < 25:
        return "green"
    elif score < 50:
        return "yellow"
    elif score < 75:
        return "orange"
    return "red"


# ─── Core Algorithm: Waiting Time Prediction ─────────────────────────────────

def predict_wait_time(
    queue_length: int,
    avg_processing_minutes: float,
    crop_complexity: float = DEFAULT_COMPLEXITY,
    active_counters: int = 1,
) -> float:
    """
    Deterministic formula for estimating waiting time in minutes.

    WaitTime = (queue_length × avg_processing_minutes × crop_complexity) / active_counters

    Returns: estimated wait in minutes (minimum 0)
    """
    if active_counters <= 0:
        active_counters = 1
    wait = (queue_length * avg_processing_minutes * crop_complexity) / active_counters
    return max(0.0, round(wait, 1))


# ─── Core Algorithm: Congestion Scoring (0-100) ───────────────────────────────

def compute_congestion_score(
    booked_count: int,
    slot_capacity: int,
    active_queue_length: int,
    daily_target: int,
    avg_processing_minutes: float,
    base_processing_minutes: float = 20.0,
) -> float:
    """
    Congestion score on a 0-100 scale where 100 = maximum congestion.

    Components:
      - 50%: Slot fill rate (booked / capacity)
      - 30%: Active queue pressure (queue / daily target)
      - 20%: Processing speed factor (actual vs base time)
    """
    fill_rate = booked_count / max(slot_capacity, 1)
    queue_pressure = active_queue_length / max(daily_target, 1)
    speed_factor = avg_processing_minutes / max(base_processing_minutes, 1)

    raw = (0.5 * fill_rate + 0.3 * queue_pressure + 0.2 * speed_factor)
    score = min(100.0, raw * 100.0)
    return round(score, 1)


# ─── Slot Score (Lower = Better) ─────────────────────────────────────────────

def compute_slot_score(
    fill_rate: float,
    wait_time: float,
    congestion: float,
    max_wait: float = 120.0,
) -> float:
    """
    Normalized composite slot score for ranking.
    All components normalized to 0-1; lower is better.
    """
    norm_fill = fill_rate                        # 0-1
    norm_wait = min(wait_time / max_wait, 1.0)  # 0-1
    norm_congestion = congestion / 100.0         # 0-1
    score = (0.4 * norm_fill + 0.35 * norm_wait + 0.25 * norm_congestion)
    return round(score, 4)


# ─── Recommendation Reason Generator ─────────────────────────────────────────

def generate_reason(
    slot: Slot,
    rank: int,
    wait_time: float,
    congestion: float,
    fill_rate: float,
    centre: ProcurementCentre,
) -> str:
    """Generate a human-readable explanation of why this slot is recommended."""
    lines = []
    label = congestion_label(congestion)

    if rank == 1:
        lines.append("⭐ Best option based on current demand patterns.")

    if fill_rate < 0.4:
        lines.append(f"Only {int(fill_rate * 100)}% of slot capacity is booked — plenty of room.")
    elif fill_rate < 0.7:
        lines.append(f"Slot is {int(fill_rate * 100)}% booked with good availability remaining.")
    else:
        lines.append(f"Slot is {int(fill_rate * 100)}% booked — limited seats left.")

    if wait_time < 15:
        lines.append(f"Predicted wait time is very short: ~{wait_time:.0f} minutes.")
    elif wait_time < 30:
        lines.append(f"Expected wait: ~{wait_time:.0f} minutes — within comfortable range.")
    else:
        lines.append(f"Estimated wait: ~{wait_time:.0f} minutes due to higher bookings.")

    lines.append(f"Congestion level: {label}.")

    if centre.processing_capacity >= 6:
        lines.append(f"{centre.name} has {centre.processing_capacity} active counters for faster processing.")

    return " ".join(lines)


# ─── Main Public API ──────────────────────────────────────────────────────────

async def get_slot_recommendations(
    db: AsyncSession,
    centre_id: int,
    target_date: date,
    crop_complexity: float = DEFAULT_COMPLEXITY,
    top_n: int = 3,
) -> list[dict]:
    """
    Return top_n recommended slots for a given centre and date.

    Each result dict contains:
      slot, rank, score, congestion_score, congestion_label,
      estimated_wait_minutes, reason
    """
    # Load centre info
    centre_result = await db.execute(
        select(ProcurementCentre).where(ProcurementCentre.id == centre_id)
    )
    centre = centre_result.scalar_one_or_none()
    if not centre:
        return []

    # Load open slots for this centre/date
    slots_result = await db.execute(
        select(Slot).where(
            Slot.centre_id == centre_id,
            Slot.slot_date == target_date,
            Slot.status == SlotStatus.OPEN,
        )
    )
    slots = slots_result.scalars().all()
    if not slots:
        return []

    # Get current active queue length for the centre
    queue_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status.in_([TokenStatus.WAITING, TokenStatus.CALLED]),
        )
    )
    active_queue = queue_result.scalar() or 0

    scored = []
    for slot in slots:
        fill_rate = slot.booked_count / max(slot.capacity, 1)
        wait_time = predict_wait_time(
            queue_length=slot.booked_count,
            avg_processing_minutes=centre.avg_processing_minutes,
            crop_complexity=crop_complexity,
            active_counters=centre.processing_capacity,
        )
        congestion = compute_congestion_score(
            booked_count=slot.booked_count,
            slot_capacity=slot.capacity,
            active_queue_length=active_queue,
            daily_target=centre.daily_capacity,
            avg_processing_minutes=centre.avg_processing_minutes,
        )
        score = compute_slot_score(fill_rate, wait_time, congestion)

        scored.append({
            "_slot": slot,
            "_centre": centre,
            "_fill_rate": fill_rate,
            "score": score,
            "congestion_score": congestion,
            "estimated_wait_minutes": wait_time,
        })

    # Sort ascending (lowest score = best)
    scored.sort(key=lambda x: x["score"])
    top = scored[:top_n]

    results = []
    for rank, item in enumerate(top, start=1):
        slot = item["_slot"]
        centre = item["_centre"]
        reason = generate_reason(
            slot=slot,
            rank=rank,
            wait_time=item["estimated_wait_minutes"],
            congestion=item["congestion_score"],
            fill_rate=item["_fill_rate"],
            centre=centre,
        )
        results.append({
            "slot": slot,
            "rank": rank,
            "score": item["score"],
            "congestion_score": item["congestion_score"],
            "congestion_label": congestion_label(item["congestion_score"]),
            "estimated_wait_minutes": item["estimated_wait_minutes"],
            "reason": reason,
            "fill_rate": item["_fill_rate"],
        })

    return results
