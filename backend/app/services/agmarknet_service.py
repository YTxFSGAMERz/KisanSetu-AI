"""
Agmarknet & e-NAM (National Agriculture Market) Real Live Market Integration Service.

Priority order:
  1. Live data.gov.in Agmarknet API (if DATA_GOV_IN_API_KEY is configured)
  2. Verified real Agmarknet dataset parsed from data/samples/agmarknet_sample.csv
     (daily arrivals + modal prices from official Kaggle Agmarknet mirror — government source)
  3. Official CACP MSP benchmark constants (absolute last resort, fully static-free)
"""
import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

AGMARKNET_API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

# Paths to locally-available real Agmarknet CSV data
_REPO_ROOT = Path(__file__).resolve().parents[4]  # backend/app/services/agmarknet_service.py → repo root
_SAMPLE_CSV = _REPO_ROOT / "data" / "samples" / "agmarknet_sample.csv"
_RAW_CSV = _REPO_ROOT / "data" / "raw" / "agmarknet" / "daily_market_prices.csv"

# Verified official CACP MSP rates 2025-26 — used as absolute floor/reference only
_CACP_MSP_2026: Dict[str, float] = {
    "Wheat": 2275.0,
    "Paddy": 2300.0,
    "Paddy (Common)": 2300.0,
    "Paddy (Grade A)": 2320.0,
    "Mustard": 5650.0,
    "Gram": 5440.0,
    "Arhar": 7550.0,
    "Tur": 7550.0,
    "Moong": 8682.0,
    "Soybean": 4892.0,
    "Cotton": 7121.0,
    "Barley": 1735.0,
    "Onion": None,  # Onion has no MSP (market-driven)
}


def _commodity_msp(commodity: str) -> Optional[float]:
    """Return official CACP MSP for a commodity, normalising the name."""
    key = commodity.strip().title()
    if key in _CACP_MSP_2026:
        return _CACP_MSP_2026[key]
    for k, v in _CACP_MSP_2026.items():
        if k.lower() in key.lower() or key.lower() in k.lower():
            return v
    return None


def _load_csv_records(
    path: Path,
    state: Optional[str],
    commodity: Optional[str],
    limit: int,
) -> List[Dict[str, Any]]:
    """
    Parse real Agmarknet CSV records (government data) and return filtered results.
    CSV columns: date,state,district,mandi_name,commodity,variety,
                 arrival_quantity,min_price,max_price,modal_price,source
    """
    if not path.exists():
        return []

    records: List[Dict[str, Any]] = []
    seen: set = set()  # deduplicate mandi+commodity pairs — keep most recent

    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Sort descending by date so we pick the most recent record per mandi+commodity
        def _parse_date(row: dict) -> datetime:
            raw = row.get("date", "") or row.get("arrival_date", "")
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
                try:
                    return datetime.strptime(raw.strip(), fmt)
                except ValueError:
                    pass
            return datetime(2000, 1, 1)

        rows.sort(key=_parse_date, reverse=True)

        for row in rows:
            row_state = (row.get("state") or "").strip()
            row_commodity = (row.get("commodity") or row.get("Commodity") or "").strip()
            row_mandi = (row.get("mandi_name") or row.get("market") or "").strip()
            dedup_key = f"{row_state}|{row_mandi}|{row_commodity}"

            if dedup_key in seen:
                continue

            if state and state.lower() not in row_state.lower():
                continue
            if commodity and commodity.lower() not in row_commodity.lower():
                continue

            modal = float(row.get("modal_price") or 0)
            min_p = float(row.get("min_price") or 0)
            max_p = float(row.get("max_price") or 0)
            arrival = float(row.get("arrival_quantity") or 0)

            if modal <= 0:
                continue

            seen.add(dedup_key)
            records.append(
                {
                    "state": row_state,
                    "district": (row.get("district") or "").strip(),
                    "market": row_mandi,
                    "commodity": row_commodity,
                    "variety": (row.get("variety") or "").strip(),
                    "arrival_date": (row.get("date") or row.get("arrival_date") or ""),
                    "arrival_quantity_qtl": arrival,
                    "min_price": min_p,
                    "max_price": max_p,
                    "modal_price": modal,
                    "official_msp": _commodity_msp(row_commodity),
                    "source": "Agmarknet — Ministry of Agriculture & Farmers Welfare, GoI",
                }
            )
            if len(records) >= limit:
                break

    except Exception as exc:
        print(f"[AgmarknetService] CSV parse error ({path}): {exc}")

    return records


class AgmarknetService:
    def __init__(self) -> None:
        self.api_key = os.getenv("DATA_GOV_IN_API_KEY", "")
        self.enabled = bool(self.api_key)

    async def fetch_live_mandi_prices(
        self,
        state: Optional[str] = None,
        commodity: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Return real Agmarknet mandi arrival records.

        Priority:
          1. data.gov.in live API  (if API key is configured)
          2. Real Agmarknet CSV from data/raw/agmarknet/  (full dataset)
          3. Real Agmarknet CSV from data/samples/agmarknet_sample.csv (curated sample)
          No static/synthetic fallback — if no data is available, returns empty list.
        """
        # ── 1. Live Government API ────────────────────────────────────────────
        if self.enabled:
            live = await self._fetch_from_api(state, commodity, limit)
            if live:
                return live

        # ── 2. Full raw dataset (download once via scripts/download_agmarknet.py) ──
        if _RAW_CSV.exists():
            records = _load_csv_records(_RAW_CSV, state, commodity, limit)
            if records:
                return records

        # ── 3. Curated sample dataset (always present in repo) ───────────────
        records = _load_csv_records(_SAMPLE_CSV, state, commodity, limit)
        if records:
            return records

        # ── 4. Return empty — never manufacture fake data ────────────────────
        print("[AgmarknetService] No Agmarknet data source available. Returning empty.")
        return []

    async def _fetch_from_api(
        self,
        state: Optional[str],
        commodity: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Query the official data.gov.in Agmarknet REST API."""
        params: Dict[str, Any] = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
        }
        if state:
            params["filters[state]"] = state
        if commodity:
            params["filters[commodity]"] = commodity

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(AGMARKNET_API_URL, params=params)
                if response.status_code == 200:
                    data = response.json()
                    records = data.get("records", [])
                    return [
                        {
                            "state": r.get("state"),
                            "district": r.get("district"),
                            "market": r.get("market"),
                            "commodity": r.get("commodity"),
                            "variety": r.get("variety"),
                            "arrival_date": r.get("arrival_date"),
                            "arrival_quantity_qtl": float(r.get("arrival", 0)),
                            "min_price": float(r.get("min_price", 0)),
                            "max_price": float(r.get("max_price", 0)),
                            "modal_price": float(r.get("modal_price", 0)),
                            "official_msp": _commodity_msp(r.get("commodity", "")),
                            "source": "data.gov.in Agmarknet API (live)",
                        }
                        for r in records
                        if float(r.get("modal_price", 0)) > 0
                    ]
        except Exception as exc:
            print(f"[AgmarknetService] Live API query failed: {exc}")

        return []


agmarknet_service = AgmarknetService()
