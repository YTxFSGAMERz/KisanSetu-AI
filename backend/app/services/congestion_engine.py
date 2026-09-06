"""
KisanSetu AI — Enhanced Congestion Engine (v2)
================================================
Extends (does NOT replace) recommendation_engine.py with:

  1. Rolling average processing time from real QueueToken history
  2. FCI-based demand index (state + commodity procurement volume)
  3. Seasonal demand weighting (Rabi/Kharif peak detection)
  4. Day-of-week demand multipliers
  5. Enhanced congestion score (0-100) with configurable thresholds
  6. CongestionLevel enum: LOW / MODERATE / HIGH / SEVERE

Integration:
  - recommendation_engine.get_slot_recommendations() is NOT modified
  - This module provides supplemental functions that API routes can call
  - congestion_engine.compute_congestion_score_v2() is a drop-in enrichment
    to the existing compute_congestion_score() in recommendation_engine.py

Usage from API route:
  from app.services.congestion_engine import (
      CongestionLevel,
      compute_congestion_score_v2,
      get_rolling_avg_processing_time,
      compute_demand_score,
      get_slot_demand_context,
  )

SIH 26032 alignment:
  This module directly enables:
  ✅ Requirement 2: Real-time queue management (live congestion scoring)
  ✅ Requirement 3: SMS/app notifications (arrival time recommendations)
  ✅ Requirement 5: Reduce congestion and waiting time at centres
"""
import json
import math
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.queue_token import QueueToken, TokenStatus
from app.models.slot import Slot, SlotStatus
from app.models.centre import ProcurementCentre
from app.services.recommendation_engine import (
    predict_wait_time,
    compute_congestion_score,
)

if TYPE_CHECKING:
    pass

# ─── Repository paths ─────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DEMAND_INDEX_FILE = _REPO_ROOT / "data" / "processed" / "procurement" / "procurement_demand_index.json"
_AGMARKNET_PARQUET = _REPO_ROOT / "data" / "processed" / "mandi_arrivals" / "agmarknet_clean.parquet"


# ─── Configurable Thresholds ──────────────────────────────────────────────────
CONGESTION_THRESHOLDS: dict[str, int] = {
    "LOW_MAX": 30,
    "MODERATE_MAX": 60,
    "HIGH_MAX": 80,
    # > HIGH_MAX → SEVERE
}

# Day-of-week demand multipliers (0=Monday, 6=Sunday)
# Based on observed agricultural procurement patterns:
# Mondays after weekend gap tend to be busier; mid-week steady; Friday slows
DAY_OF_WEEK_MULTIPLIERS: dict[int, float] = {
    0: 1.20,  # Monday   — high (post-weekend accumulation)
    1: 1.05,  # Tuesday  — slightly above average
    2: 1.00,  # Wednesday — baseline
    3: 0.95,  # Thursday
    4: 0.90,  # Friday   — farmers may prefer early-week
    5: 0.80,  # Saturday — reduced operations
    6: 0.50,  # Sunday   — typically closed/minimal
}

# Seasonal multipliers by month (approximate Rabi/Kharif procurement peaks)
# Rabi peak: March–May (wheat, mustard)
# Kharif peak: October–January (paddy, soyabean, cotton)
MONTH_DEMAND_MULTIPLIERS: dict[int, float] = {
    1: 1.10,  # Jan   — KMS paddy procurement active
    2: 1.00,  # Feb   — transitional
    3: 1.30,  # Mar   — Rabi starts (wheat)
    4: 1.40,  # Apr   — Rabi peak (wheat, mustard)
    5: 1.20,  # May   — Rabi winding down
    6: 0.80,  # Jun   — off-season
    7: 0.70,  # Jul   — off-season
    8: 0.75,  # Aug   — off-season
    9: 0.85,  # Sep   — Kharif harvesting begins
    10: 1.20, # Oct   — KMS paddy peak
    11: 1.30, # Nov   — KMS paddy/soyabean peak
    12: 1.15, # Dec   — KMS active
}


# ─── CongestionLevel Enum ─────────────────────────────────────────────────────

class CongestionLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


def congestion_level_from_score(score: float) -> CongestionLevel:
    """Map 0-100 score to CongestionLevel using configurable thresholds."""
    if score <= CONGESTION_THRESHOLDS["LOW_MAX"]:
        return CongestionLevel.LOW
    elif score <= CONGESTION_THRESHOLDS["MODERATE_MAX"]:
        return CongestionLevel.MODERATE
    elif score <= CONGESTION_THRESHOLDS["HIGH_MAX"]:
        return CongestionLevel.HIGH
    return CongestionLevel.SEVERE


def congestion_color(level: CongestionLevel) -> str:
    return {
        CongestionLevel.LOW: "green",
        CongestionLevel.MODERATE: "yellow",
        CongestionLevel.HIGH: "orange",
        CongestionLevel.SEVERE: "red",
    }[level]


# ─── Procurement Demand Index ─────────────────────────────────────────────────

_demand_index_cache: dict | None = None


def _load_demand_index() -> dict:
    """Load FCI-based procurement demand index (cached after first load)."""
    global _demand_index_cache
    if _demand_index_cache is not None:
        return _demand_index_cache

    if _DEMAND_INDEX_FILE.exists():
        with open(_DEMAND_INDEX_FILE, encoding="utf-8") as f:
            _demand_index_cache = json.load(f)
    else:
        _demand_index_cache = {}

    return _demand_index_cache


_mandi_arrival_cache: Optional[dict[tuple[str, str], float]] = None


def _load_mandi_arrivals() -> dict[tuple[str, str], float]:
    """Load average mandi arrival quantities from processed Agmarknet data if present."""
    global _mandi_arrival_cache
    if _mandi_arrival_cache is not None:
        return _mandi_arrival_cache

    _mandi_arrival_cache = {}
    if _AGMARKNET_PARQUET.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(_AGMARKNET_PARQUET)
            if "state" in df.columns and "commodity" in df.columns and "arrival_quantity" in df.columns:
                grouped = df.groupby(["state", "commodity"])["arrival_quantity"].mean()
                for (st, comm), val in grouped.items():
                    _mandi_arrival_cache[(str(st).strip().title(), str(comm).strip().title())] = float(val)
        except Exception:
            pass

    return _mandi_arrival_cache


def compute_demand_score(
    state: str,
    commodity: str,
    procurement_date: Optional[date] = None,
) -> float:
    """
    Compute a normalized demand score (0-100) for a state/commodity/date.

    Components:
      1. FCI-based procurement demand index (how much of this commodity this state procures)
      2. Seasonal multiplier (month-based Rabi/Kharif weighting)
      3. Day-of-week multiplier
      4. Mandi arrival pressure (from Agmarknet clean dataset if available)

    Returns: float 0.0-100.0
    """
    index = _load_demand_index()
    key = f"{state}|{commodity}"
    base_demand = index.get(key, 25.0)  # Default to 25% if unknown

    target_date = procurement_date or date.today()
    seasonal_mult = MONTH_DEMAND_MULTIPLIERS.get(target_date.month, 1.0)
    dow_mult = DAY_OF_WEEK_MULTIPLIERS.get(target_date.weekday(), 1.0)

    raw_score = base_demand * seasonal_mult * dow_mult

    # Fine-tune with Agmarknet average mandi arrival volume if present
    arrivals = _load_mandi_arrivals()
    avg_arr = arrivals.get((state.strip().title(), commodity.strip().title()))
    if avg_arr is not None and avg_arr > 0:
        # Scale arrival volume (e.g. 50-300 tonnes) to a modifier between 0.85 and 1.25
        arrival_mult = min(1.25, max(0.85, 0.85 + (avg_arr / 250.0) * 0.40))
        raw_score *= arrival_mult

    return round(min(100.0, max(0.0, raw_score)), 1)


# ─── Rolling Average Processing Time ─────────────────────────────────────────

async def get_rolling_avg_processing_time(
    db: AsyncSession,
    centre_id: int,
    lookback_days: int = 7,
    fallback_minutes: float = 20.0,
) -> tuple[float, str]:
    """
    Compute rolling average processing time from real QueueToken operational data.

    Returns: (avg_minutes, source)
      source is "HISTORICAL" if real data exists, "FALLBACK" otherwise.

    Design:
      - Uses COMPLETED tokens where processing_start_time and completed_at are both set
      - Falls back to centre.avg_processing_minutes if insufficient data
      - Never permanently hardcodes a processing time when real history exists
    """
    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    result = await db.execute(
        select(QueueToken).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status == TokenStatus.COMPLETED,
            QueueToken.processing_start_time.isnot(None),
            QueueToken.completed_at.isnot(None),
            QueueToken.processing_start_time >= since,
        )
    )
    tokens = result.scalars().all()

    if len(tokens) >= 5:  # Minimum sample size for reliable average
        durations = []
        for t in tokens:
            if t.processing_start_time and t.completed_at:
                delta = (t.completed_at - t.processing_start_time).total_seconds() / 60.0
                if 0.5 <= delta <= 120:  # Sanity-check: 30s to 2h
                    durations.append(delta)

        if durations:
            avg = sum(durations) / len(durations)
            return round(avg, 1), "HISTORICAL"

    return fallback_minutes, "FALLBACK"


# ─── Enhanced Congestion Score ────────────────────────────────────────────────

def compute_congestion_score_v2(
    booked_count: int,
    slot_capacity: int,
    active_queue_length: int,
    daily_target: int,
    avg_processing_minutes: float,
    demand_score: float = 50.0,
    base_processing_minutes: float = 20.0,
) -> float:
    """
    Enhanced congestion score on a 0-100 scale (supersedes recommendation_engine version).

    Components (configurable weights):
      40%: Slot fill rate              — how full is this slot?
      25%: Active queue pressure       — how many are already waiting?
      15%: Processing speed factor     — how fast is the centre processing?
      20%: External demand score       — based on FCI data + seasonality + DoW

    Args:
        booked_count:           Bookings in this slot
        slot_capacity:          Max capacity of this slot
        active_queue_length:    Currently waiting farmers at centre
        daily_target:           Centre's daily farmer capacity
        avg_processing_minutes: Rolling avg or fallback processing time
        demand_score:           0-100 from compute_demand_score()
        base_processing_minutes: Baseline reference for speed factor

    Returns: float 0.0–100.0
    """
    fill_rate = booked_count / max(slot_capacity, 1)
    queue_pressure = min(active_queue_length / max(daily_target, 1), 1.0)
    speed_factor = min(avg_processing_minutes / max(base_processing_minutes, 1), 2.0)
    demand_factor = demand_score / 100.0

    raw = (
        0.40 * fill_rate +
        0.25 * queue_pressure +
        0.15 * speed_factor +
        0.20 * demand_factor
    )
    score = min(100.0, raw * 100.0)
    return round(score, 1)


# ─── Predicted Wait Time ──────────────────────────────────────────────────────

def compute_predicted_wait_time(
    queue_length: int,
    avg_processing_minutes: float,
    active_counters: int,
    crop_complexity: float = 1.0,
    demand_score: float = 50.0,
) -> float:
    """
    Enhanced wait time prediction incorporating demand score.

    Formula:
      BaseWait = (queue_length × avg_processing_minutes × crop_complexity) / active_counters
      DemandFactor = 1.0 + (demand_score / 100.0) × 0.30
      PredictedWait = BaseWait × DemandFactor

    The demand factor adds up to 30% extra expected wait during peak demand periods.
    """
    if active_counters <= 0:
        active_counters = 1

    base_wait = (queue_length * avg_processing_minutes * crop_complexity) / active_counters
    demand_factor = 1.0 + (demand_score / 100.0) * 0.30
    predicted = base_wait * demand_factor

    return round(max(0.0, predicted), 1)


# ─── Recommended Arrival Window ───────────────────────────────────────────────

def compute_recommended_arrival_offset(
    congestion_score: float,
    slot_start_minutes_from_now: int,
) -> dict:
    """
    Given a congestion score, compute how far before the slot the farmer
    should arrive to minimize physical wait time.

    Returns a dict with:
      arrive_minutes_before_slot: int
      message: str  (for SMS/notification)
    """
    level = congestion_level_from_score(congestion_score)

    offsets = {
        CongestionLevel.LOW: 5,
        CongestionLevel.MODERATE: 10,
        CongestionLevel.HIGH: 20,
        CongestionLevel.SEVERE: 30,
    }
    arrive_before = offsets[level]

    messages = {
        CongestionLevel.LOW: f"Low congestion expected. Arrive {arrive_before} min before your slot.",
        CongestionLevel.MODERATE: f"Moderate queue expected. Arrive {arrive_before} min before your slot for smooth processing.",
        CongestionLevel.HIGH: f"High demand at centre. Arrive {arrive_before} min early to avoid delays.",
        CongestionLevel.SEVERE: f"⚠️ Very high congestion. Arrive {arrive_before} min before slot or consider rebooking a less crowded slot.",
    }

    return {
        "congestion_level": level.value,
        "arrive_minutes_before_slot": arrive_before,
        "message": messages[level],
    }


# ─── Full Slot Demand Context ─────────────────────────────────────────────────

async def get_slot_demand_context(
    db: AsyncSession,
    slot: Slot,
    centre: ProcurementCentre,
    commodity: str = "Wheat",
    procurement_date: Optional[date] = None,
) -> dict:
    """
    Compute the full demand context for a slot including:
      - Rolling avg processing time (from real history or fallback)
      - Demand score (FCI + seasonality + DoW)
      - Enhanced congestion score v2
      - Predicted wait time
      - Recommended arrival offset
      - Congestion level and color

    This is the primary function for enriching slot recommendations
    with government data-backed demand intelligence.
    """
    # Rolling avg processing time
    avg_minutes, time_source = await get_rolling_avg_processing_time(
        db, centre.id, fallback_minutes=centre.avg_processing_minutes
    )

    # External demand score
    target_date = procurement_date or (slot.slot_date if hasattr(slot, "slot_date") else date.today())
    demand_score = compute_demand_score(centre.state, commodity, target_date)

    # Active queue
    queue_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre.id,
            QueueToken.status.in_([TokenStatus.WAITING, TokenStatus.CALLED]),
        )
    )
    active_queue = queue_result.scalar() or 0

    # Enhanced congestion score
    congestion = compute_congestion_score_v2(
        booked_count=slot.booked_count,
        slot_capacity=slot.capacity,
        active_queue_length=active_queue,
        daily_target=centre.daily_capacity,
        avg_processing_minutes=avg_minutes,
        demand_score=demand_score,
    )

    fill_rate = slot.booked_count / max(slot.capacity, 1)

    # Predicted wait time
    wait_time = compute_predicted_wait_time(
        queue_length=slot.booked_count,
        avg_processing_minutes=avg_minutes,
        active_counters=centre.processing_capacity,
        demand_score=demand_score,
    )

    level = congestion_level_from_score(congestion)
    arrival_advice = compute_recommended_arrival_offset(congestion, 0)

    return {
        "congestion_score": congestion,
        "congestion_level": level.value,
        "congestion_color": congestion_color(level),
        "estimated_wait_minutes": wait_time,
        "demand_score": demand_score,
        "fill_rate": round(fill_rate, 3),
        "active_queue_length": active_queue,
        "avg_processing_minutes": avg_minutes,
        "processing_time_source": time_source,
        "arrival_advice": arrival_advice,
    }
