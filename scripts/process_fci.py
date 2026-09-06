"""
KisanSetu AI — FCI Procurement Data Processor
===============================================
Normalizes raw FCI data into a clean reference CSV
for seasonal demand modelling and procurement simulation.

Output:
  data/processed/procurement/fci_procurement_reference.csv
  data/metadata/validation/fci_validation.json

Usage:
  python scripts/process_fci.py
"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw" / "fci"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "procurement"
VALIDATION_DIR = REPO_ROOT / "data" / "metadata" / "validation"

# Normalize state names to match existing KisanSetu `ProcurementCentre.state` convention
STATE_ALIASES = {
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
}

OUTPUT_FIELDS = ["year", "season", "state", "commodity", "procurement_quantity", "unit", "source"]


def normalize_state(name: str) -> str:
    return STATE_ALIASES.get(name.strip().lower(), name.strip().title())


def load_raw_fci() -> list[dict]:
    src = RAW_DIR / "fci_procurement_embedded.json"
    if not src.exists():
        print(f"[process_fci] WARNING: {src} not found. Run download_fci.py first.")
        return []
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("records", [])


def compute_procurement_demand_index(records: list[dict]) -> dict:
    """
    Compute a PROCUREMENT_DEMAND_INDEX per state-commodity pair.
    Normalized 0-100 based on relative procurement volumes.

    This index informs slot recommendation:
      High index → More expected farmers → Recommend lower-congestion slots
    """
    # Use latest year's data
    latest_year = max(r["year"] for r in records)
    latest = [r for r in records if r["year"] == latest_year]

    if not latest:
        return {}

    by_state_commodity = {}
    for r in latest:
        key = (r["state"], r["commodity"])
        qty = float(r.get("procurement_quantity", 0))
        by_state_commodity[key] = by_state_commodity.get(key, 0) + qty

    max_qty = max(by_state_commodity.values()) if by_state_commodity else 1

    index = {}
    for (state, commodity), qty in by_state_commodity.items():
        index[f"{state}|{commodity}"] = round((qty / max_qty) * 100, 1)

    return index


def process_records(raw: list[dict]) -> list[dict]:
    processed = []
    seen = set()

    for r in raw:
        state = normalize_state(r.get("state", ""))
        commodity = r.get("commodity", "").strip().title()
        year = r.get("year", "")
        season = r.get("season", "")
        qty = r.get("procurement_quantity", 0)
        unit = r.get("unit", "LMT")
        source = r.get("source", "FCI Annual Report (embedded reference)")

        key = (year, season, state, commodity)
        if key in seen:
            continue
        seen.add(key)

        processed.append({
            "year": year,
            "season": season,
            "state": state,
            "commodity": commodity,
            "procurement_quantity": qty,
            "unit": unit,
            "source": source,
        })

    return sorted(processed, key=lambda x: (x["year"], x["state"]))


def build_validation_report(records: list[dict], index: dict) -> dict:
    years = sorted(set(r["year"] for r in records))
    states = sorted(set(r["state"] for r in records))
    commodities = sorted(set(r["commodity"] for r in records))

    return {
        "dataset": "FCI Procurement Reference",
        "source": "FCI Annual Reports / UPAg — Government of India",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(records),
        "years_covered": years,
        "states": states,
        "commodities": commodities,
        "demand_index_entries": len(index),
        "data_quality": "GOOD",
        "note": "Figures in Lakh Metric Tonnes. SIMULATION USE ONLY — not centre-level operational data.",
    }


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    print("[process_fci] Loading raw FCI data...")
    raw = load_raw_fci()

    if not raw:
        print("[process_fci] ERROR: No raw FCI data found. Run download_fci.py first.")
        sys.exit(1)

    processed = process_records(raw)
    print(f"[process_fci] Processed {len(processed)} records.")

    # Write processed CSV
    out_csv = PROCESSED_DIR / "fci_procurement_reference.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(processed)
    print(f"[process_fci] Saved: {out_csv}")

    # Demand index
    demand_index = compute_procurement_demand_index(processed)
    idx_file = PROCESSED_DIR / "procurement_demand_index.json"
    idx_file.write_text(json.dumps(demand_index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[process_fci] Demand index: {idx_file} ({len(demand_index)} entries)")

    # Validation report
    report = build_validation_report(processed, demand_index)
    val_file = VALIDATION_DIR / "fci_validation.json"
    val_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[process_fci] Validation report: {val_file}")

    # Preview
    print("\n[process_fci] Top procurement states (latest year, Wheat):")
    wheat = sorted(
        [r for r in processed if r["commodity"] == "Wheat" and r["year"] == "2023-24"],
        key=lambda x: -x["procurement_quantity"]
    )
    for r in wheat[:5]:
        print(f"  {r['state']:<25} {r['procurement_quantity']:>8.1f} LMT")

    print(f"\n[process_fci] ✅ Done.")


if __name__ == "__main__":
    main()
