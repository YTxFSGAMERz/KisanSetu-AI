"""
KisanSetu AI — Agmarknet Data Processor
=========================================
Normalizes raw Agmarknet daily mandi arrival and price data.

Input:  data/raw/agmarknet/daily_market_prices.csv  (from Kaggle download)
Output: data/processed/mandi_arrivals/agmarknet_clean.parquet
        data/samples/agmarknet_sample.csv (100 rows, committed to git)
        data/metadata/validation/agmarknet_validation.json

Usage:
  python scripts/process_agmarknet.py
  python scripts/process_agmarknet.py --no-parquet   # CSV only (no pyarrow needed)
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw" / "agmarknet"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "mandi_arrivals"
SAMPLES_DIR = REPO_ROOT / "data" / "samples"
VALIDATION_DIR = REPO_ROOT / "data" / "metadata" / "validation"

OUTPUT_FIELDS = [
    "date", "state", "district", "mandi_name", "commodity", "variety",
    "arrival_quantity", "min_price", "max_price", "modal_price", "source",
]

# Normalize state names to consistent title case
STATE_ALIASES = {
    "andhra pradesh": "Andhra Pradesh",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "chhattisgarh": "Chhattisgarh",
    "bihar": "Bihar",
}

COMMODITY_ALIASES = {
    "wheat": "Wheat", "gehun": "Wheat",
    "paddy": "Paddy", "rice": "Rice",
    "maize": "Maize", "makka": "Maize", "corn": "Maize",
    "soybean": "Soyabean", "soyabean": "Soyabean",
    "mustard": "Mustard", "rapeseed": "Mustard",
    "gram": "Gram", "chana": "Gram",
    "tur": "Tur", "arhar": "Tur", "pigeon pea": "Tur",
    "moong": "Moong", "green gram": "Moong",
    "groundnut": "Groundnut",
    "cotton": "Cotton",
    "onion": "Onion", "pyaz": "Onion",
    "tomato": "Tomato",
    "potato": "Potato",
    "bajra": "Bajra", "pearl millet": "Bajra",
    "jowar": "Jowar", "sorghum": "Jowar",
}


def normalize_state(s: str) -> str:
    return STATE_ALIASES.get(s.strip().lower(), s.strip().title())


def normalize_commodity(c: str) -> str:
    key = c.strip().lower()
    for alias, standard in COMMODITY_ALIASES.items():
        if alias in key:
            return standard
    return c.strip().title()


def detect_schema(header: list[str]) -> dict[str, str]:
    """Auto-detect column mapping from CSV header."""
    h = [c.lower().strip().replace(" ", "_").replace("-", "_") for c in header]
    mapping = {}

    candidates = {
        "date": ["arrival_date", "date", "price_date"],
        "state": ["state", "state_name"],
        "district": ["district", "district_name"],
        "mandi_name": ["market", "mandi", "market_name", "mandi_name"],
        "commodity": ["commodity", "commodity_name", "crop"],
        "variety": ["variety", "grade"],
        "arrival_quantity": ["arrivals", "arrival_qty", "arrival_quantity", "quantity", "arrivals_tonnes"],
        "min_price": ["min_price", "minimum_price", "min"],
        "max_price": ["max_price", "maximum_price", "max"],
        "modal_price": ["modal_price", "mode_price", "modal"],
    }

    for field, options in candidates.items():
        for opt in options:
            if opt in h:
                mapping[field] = header[h.index(opt)]
                break

    return mapping


def safe_float(val) -> float | None:
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def process_agmarknet(raw_file: Path, max_rows: int = None) -> list[dict]:
    """Load, validate, and normalize Agmarknet CSV."""
    print(f"[process_agmarknet] Reading: {raw_file}")

    # Detect encoding
    encoding = "utf-8"
    try:
        with open(raw_file, encoding="utf-8", errors="strict") as f:
            f.read(8192)
    except UnicodeDecodeError:
        encoding = "latin-1"

    records = []
    seen = set()
    null_counts = {f: 0 for f in OUTPUT_FIELDS}
    schema = {}

    with open(raw_file, encoding=encoding, newline="", errors="replace") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        schema = detect_schema(header)
        print(f"[process_agmarknet] Detected schema: {schema}")

        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break

            date_val = str(row.get(schema.get("date", ""), "")).strip()
            state = normalize_state(str(row.get(schema.get("state", ""), "")).strip())
            district = str(row.get(schema.get("district", ""), "")).strip().title()
            mandi = str(row.get(schema.get("mandi_name", ""), "")).strip().title()
            commodity = normalize_commodity(str(row.get(schema.get("commodity", ""), "")).strip())
            variety = str(row.get(schema.get("variety", ""), "FAQ")).strip() or "FAQ"
            arrival_qty = safe_float(row.get(schema.get("arrival_quantity", ""), 0))
            min_price = safe_float(row.get(schema.get("min_price", ""), None))
            max_price = safe_float(row.get(schema.get("max_price", ""), None))
            modal_price = safe_float(row.get(schema.get("modal_price", ""), None))

            if not date_val or not state or not mandi or not commodity:
                continue
            if modal_price is None and min_price is None:
                continue

            # Deduplication
            key = (date_val, state, mandi, commodity, variety)
            if key in seen:
                continue
            seen.add(key)

            rec = {
                "date": date_val,
                "state": state,
                "district": district,
                "mandi_name": mandi,
                "commodity": commodity,
                "variety": variety,
                "arrival_quantity": arrival_qty or 0.0,
                "min_price": min_price,
                "max_price": max_price,
                "modal_price": modal_price,
                "source": "Agmarknet (via Kaggle mirror)",
            }

            # Count nulls
            for field in OUTPUT_FIELDS:
                if rec.get(field) is None:
                    null_counts[field] += 1

            records.append(rec)

    return records, null_counts, schema


def build_validation_report(records, null_counts, raw_file) -> dict:
    if not records:
        return {"status": "NO_DATA"}

    commodities = sorted(set(r["commodity"] for r in records))
    states = sorted(set(r["state"] for r in records))
    dates = sorted(r["date"] for r in records if r["date"])

    return {
        "dataset": "Agmarknet Daily Mandi Prices (Kaggle Mirror)",
        "original_source": "https://agmarknet.gov.in",
        "mirror_source": "https://www.kaggle.com/datasets/srinathankumar/daily-market-prices-of-commodity-india",
        "raw_file": str(raw_file.name),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(records),
        "unique_commodities": len(commodities),
        "commodities": commodities[:20],
        "unique_states": len(states),
        "states": states,
        "date_range": {"min": dates[0] if dates else None, "max": dates[-1] if dates else None},
        "null_counts": null_counts,
        "data_quality": "GOOD" if all(v == 0 for k, v in null_counts.items() if k in ["date", "state", "mandi_name", "commodity"]) else "WARNINGS_PRESENT",
    }


def main():
    parser = argparse.ArgumentParser(description="Process Agmarknet data")
    parser.add_argument("--no-parquet", action="store_true", help="Skip parquet output (CSV only)")
    parser.add_argument("--max-rows", type=int, default=None, help="Limit rows for testing")
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    raw_file = RAW_DIR / "daily_market_prices.csv"

    if not raw_file.exists():
        # Try any CSV in the raw dir
        csvs = list(RAW_DIR.glob("*.csv"))
        if csvs:
            raw_file = csvs[0]
            print(f"[process_agmarknet] Using: {raw_file.name}")
        else:
            print(f"[process_agmarknet] ERROR: No raw CSV found in {RAW_DIR}")
            print("[process_agmarknet] Run: python scripts/download_agmarknet.py")
            print("[process_agmarknet] Or manually place CSV in data/raw/agmarknet/")
            sys.exit(1)

    records, null_counts, schema = process_agmarknet(raw_file, args.max_rows)
    print(f"[process_agmarknet] Clean records: {len(records):,}")

    if not records:
        print("[process_agmarknet] ERROR: No valid records after processing.")
        sys.exit(1)

    # Save sample CSV (committed to git)
    sample_csv = SAMPLES_DIR / "agmarknet_sample.csv"
    with open(sample_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(records[:100])
    print(f"[process_agmarknet] Sample CSV: {sample_csv} (100 rows)")

    # Save parquet (if pyarrow available and not disabled)
    if not args.no_parquet:
        try:
            import pandas as pd
            df = pd.DataFrame(records)
            out_parquet = PROCESSED_DIR / "agmarknet_clean.parquet"
            df.to_parquet(out_parquet, index=False, engine="pyarrow")
            size_mb = out_parquet.stat().st_size / 1_048_576
            print(f"[process_agmarknet] Parquet: {out_parquet} ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"[process_agmarknet] WARNING: Could not write parquet: {e}")
            print("[process_agmarknet] Writing CSV fallback...")
            out_csv = PROCESSED_DIR / "agmarknet_clean.csv"
            with open(out_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
                writer.writeheader()
                writer.writerows(records)
            print(f"[process_agmarknet] CSV fallback: {out_csv}")

    # Validation report
    report = build_validation_report(records, null_counts, raw_file)
    val_file = VALIDATION_DIR / "agmarknet_validation.json"
    val_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[process_agmarknet] Validation: {val_file}")

    print(f"\n[process_agmarknet] ✅ Done. {len(records):,} records processed.")


if __name__ == "__main__":
    main()
