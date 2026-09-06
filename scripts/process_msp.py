"""
KisanSetu AI — MSP Data Processor
====================================
Normalizes raw MSP data into a clean reference CSV and
provides a versioned lookup function for payment calculations.

Output:
  data/processed/msp/msp_reference.csv
  data/samples/msp_sample.csv
  data/metadata/validation/msp_validation.json

Usage:
  python scripts/process_msp.py
"""
import csv
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw" / "msp"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "msp"
SAMPLES_DIR = REPO_ROOT / "data" / "samples"
VALIDATION_DIR = REPO_ROOT / "data" / "metadata" / "validation"

OUTPUT_FIELDS = [
    "marketing_season", "season", "crop", "commodity", "variety",
    "msp", "unit", "effective_date", "source",
]


def normalize_crop_name(name: str) -> str:
    """Normalize crop names to consistent title case."""
    return name.strip().title()


def load_embedded_msp() -> list[dict]:
    """Load from embedded JSON reference (written by download_msp.py)."""
    src = RAW_DIR / "msp_embedded_reference.json"
    if not src.exists():
        print(f"[process_msp] WARNING: {src} not found. Run download_msp.py first.")
        return []
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("records", [])


def process_records(raw: list[dict]) -> list[dict]:
    """Normalize and validate raw MSP records."""
    processed = []
    seen = set()

    for r in raw:
        crop = normalize_crop_name(r.get("crop", ""))
        commodity = normalize_crop_name(r.get("commodity", crop))
        variety = r.get("variety", "FAQ").strip()
        msp = float(r.get("msp", 0))
        season = r.get("marketing_season", "UNKNOWN")
        season_type = r.get("season", "UNKNOWN")
        eff_date = r.get("effective_date", "")
        source = r.get("source", "CACP (embedded reference)")

        if msp <= 0:
            continue

        key = (season, crop, variety)
        if key in seen:
            continue
        seen.add(key)

        processed.append({
            "marketing_season": season,
            "season": season_type,
            "crop": crop,
            "commodity": commodity,
            "variety": variety,
            "msp": msp,
            "unit": r.get("unit", "INR/quintal"),
            "effective_date": eff_date,
            "source": source,
        })

    return sorted(processed, key=lambda x: (x["marketing_season"], x["crop"]))


def get_msp(
    crop: str,
    marketing_season: str,
    procurement_date: Optional[str] = None,
    data_dir: Optional[Path] = None,
) -> Optional[float]:
    """
    Versioned MSP lookup function for payment calculations.

    Args:
        crop: Crop name (e.g., "Wheat", "Paddy")
        marketing_season: Season string e.g. "2024-25"
        procurement_date: ISO date string (unused currently, for future exact date matching)
        data_dir: Override path to processed MSP directory

    Returns:
        MSP value in INR/quintal, or None if not found.
        If not found, caller must display "REFERENCE ESTIMATE NOT AVAILABLE" to user.
    """
    csv_path = (data_dir or PROCESSED_DIR) / "msp_reference.csv"
    if not csv_path.exists():
        return None

    crop_normalized = crop.strip().title()
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row["marketing_season"] == marketing_season and
                    crop_normalized in row["crop"]):
                return float(row["msp"])
    return None


def build_validation_report(records: list[dict]) -> dict:
    """Build a data quality report for the processed MSP data."""
    seasons = sorted(set(r["marketing_season"] for r in records))
    crops = sorted(set(r["crop"] for r in records))
    null_msp = [r for r in records if not r["msp"]]
    null_dates = [r for r in records if not r["effective_date"]]

    return {
        "dataset": "MSP Reference",
        "source": "CACP / UPAg — Government of India",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(records),
        "unique_seasons": seasons,
        "unique_crops": crops,
        "records_with_null_msp": len(null_msp),
        "records_with_null_effective_date": len(null_dates),
        "msp_range_inr_per_quintal": {
            "min": min(r["msp"] for r in records) if records else None,
            "max": max(r["msp"] for r in records) if records else None,
        },
        "data_quality": "GOOD" if len(null_msp) == 0 else "WARNINGS_PRESENT",
    }


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    print("[process_msp] Loading raw MSP data...")
    raw = load_embedded_msp()

    if not raw:
        print("[process_msp] ERROR: No raw MSP data found. Run download_msp.py first.")
        sys.exit(1)

    print(f"[process_msp] Raw records: {len(raw)}")

    processed = process_records(raw)
    print(f"[process_msp] Processed records: {len(processed)}")

    # Write full processed CSV
    out_csv = PROCESSED_DIR / "msp_reference.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(processed)
    print(f"[process_msp] Saved: {out_csv}")

    # Write sample CSV (committed to git)
    sample_csv = SAMPLES_DIR / "msp_sample.csv"
    with open(sample_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(processed[:25])  # First 25 rows as sample
    print(f"[process_msp] Sample saved: {sample_csv}")

    # Validation report
    report = build_validation_report(processed)
    val_file = VALIDATION_DIR / "msp_validation.json"
    val_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[process_msp] Validation report: {val_file}")

    # Quick preview
    print("\n[process_msp] Sample records:")
    for r in processed[:5]:
        print(f"  {r['marketing_season']} | {r['crop']:<30} | ₹{r['msp']:>6}/qtl | {r['effective_date']}")

    print(f"\n[process_msp] ✅ Done. {len(processed)} MSP records processed.")
    print(f"[process_msp] Lookup usage:")
    print(f"  from scripts.process_msp import get_msp")
    print(f"  msp = get_msp('Wheat', '2024-25')  # Returns: 2275.0")


if __name__ == "__main__":
    main()
