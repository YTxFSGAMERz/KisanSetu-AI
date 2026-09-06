"""
KisanSetu AI — eNAM Mandi Reference Data
==========================================
Provides curated reference data for eNAM-integrated mandis across India.

Source:
  eNAM (Electronic National Agriculture Market): https://enam.gov.in
  National Agriculture Market — Ministry of Agriculture & Farmers Welfare, GoI

This script does NOT:
  - Collect farmer PII
  - Collect trader PII
  - Access authenticated endpoints
  - Scrape non-public data

It provides a curated list of major APMC/mandi centers for use as:
  - Location seed data for procurement centres
  - Reference mapping between districts and market infrastructure
  - Clearly labeled MANDI_REFERENCE_DATA (not procurement centre operational data)

Usage:
  python scripts/fetch_enam_reference.py
"""
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "centres"
META_DIR = REPO_ROOT / "data" / "metadata"
SOURCES_FILE = META_DIR / "sources.json"
HEADERS = {"User-Agent": "KisanSetu-AI Research Pipeline / SIH 26032"}


def load_sources() -> dict:
    if SOURCES_FILE.exists():
        with open(SOURCES_FILE) as f:
            return json.load(f)
    return {}


def save_sources(sources: dict):
    META_DIR.mkdir(parents=True, exist_ok=True)
    with open(SOURCES_FILE, "w") as f:
        json.dump(sources, f, indent=2)


def try_enam_public_api() -> list[dict] | None:
    """Attempt to fetch public eNAM mandi statistics."""
    # eNAM public dashboard API (no authentication needed)
    url = "https://enam.gov.in/web/dashboard/trade-data"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data
    except Exception:
        pass
    return None


def get_curated_enam_reference() -> list[dict]:
    """
    Curated list of major APMC / eNAM-integrated mandis.
    Source: eNAM public website (enam.gov.in/web/activities/state-wise-mandi.html)
    Data type: MANDI_REFERENCE_DATA
    Note: Not all of these are necessarily procurement centres for wheat/paddy.
          KisanSetu may use these as candidate locations for seeding demo centres.
    """
    return [
        # Punjab
        {"centre_reference_id": "ENAM-PB-001", "centre_name": "Khanna (Ludhiana)", "state": "Punjab", "district": "Ludhiana", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-PB-002", "centre_name": "Amritsar", "state": "Punjab", "district": "Amritsar", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-PB-003", "centre_name": "Patiala", "state": "Punjab", "district": "Patiala", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-PB-004", "centre_name": "Ferozepur", "state": "Punjab", "district": "Ferozepur", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-PB-005", "centre_name": "Barnala", "state": "Punjab", "district": "Barnala", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Haryana
        {"centre_reference_id": "ENAM-HR-001", "centre_name": "Karnal", "state": "Haryana", "district": "Karnal", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-HR-002", "centre_name": "Ambala", "state": "Haryana", "district": "Ambala", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-HR-003", "centre_name": "Hisar", "state": "Haryana", "district": "Hisar", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-HR-004", "centre_name": "Sirsa", "state": "Haryana", "district": "Sirsa", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-HR-005", "centre_name": "Kaithal", "state": "Haryana", "district": "Kaithal", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-HR-006", "centre_name": "Fatehabad", "state": "Haryana", "district": "Fatehabad", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Madhya Pradesh
        {"centre_reference_id": "ENAM-MP-001", "centre_name": "Indore (Choithram)", "state": "Madhya Pradesh", "district": "Indore", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-MP-002", "centre_name": "Bhopal", "state": "Madhya Pradesh", "district": "Bhopal", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-MP-003", "centre_name": "Vidisha", "state": "Madhya Pradesh", "district": "Vidisha", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-MP-004", "centre_name": "Sehore", "state": "Madhya Pradesh", "district": "Sehore", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-MP-005", "centre_name": "Hoshangabad (Narmadapuram)", "state": "Madhya Pradesh", "district": "Narmadapuram", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Uttar Pradesh
        {"centre_reference_id": "ENAM-UP-001", "centre_name": "Lucknow", "state": "Uttar Pradesh", "district": "Lucknow", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-UP-002", "centre_name": "Agra", "state": "Uttar Pradesh", "district": "Agra", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-UP-003", "centre_name": "Kanpur", "state": "Uttar Pradesh", "district": "Kanpur", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-UP-004", "centre_name": "Varanasi", "state": "Uttar Pradesh", "district": "Varanasi", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-UP-005", "centre_name": "Bareilly", "state": "Uttar Pradesh", "district": "Bareilly", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Rajasthan
        {"centre_reference_id": "ENAM-RJ-001", "centre_name": "Sri Ganganagar", "state": "Rajasthan", "district": "Sri Ganganagar", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-RJ-002", "centre_name": "Jaipur (Muhana)", "state": "Rajasthan", "district": "Jaipur", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-RJ-003", "centre_name": "Jodhpur", "state": "Rajasthan", "district": "Jodhpur", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-RJ-004", "centre_name": "Bikaner", "state": "Rajasthan", "district": "Bikaner", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Maharashtra
        {"centre_reference_id": "ENAM-MH-001", "centre_name": "Lasalgaon (Nashik)", "state": "Maharashtra", "district": "Nashik", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-MH-002", "centre_name": "Pune (Gultekdi)", "state": "Maharashtra", "district": "Pune", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-MH-003", "centre_name": "Nagpur", "state": "Maharashtra", "district": "Nagpur", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Gujarat
        {"centre_reference_id": "ENAM-GJ-001", "centre_name": "Unjha (Mehsana)", "state": "Gujarat", "district": "Mehsana", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-GJ-002", "centre_name": "Ahmedabad", "state": "Gujarat", "district": "Ahmedabad", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-GJ-003", "centre_name": "Rajkot", "state": "Gujarat", "district": "Rajkot", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Telangana
        {"centre_reference_id": "ENAM-TS-001", "centre_name": "Nizamabad", "state": "Telangana", "district": "Nizamabad", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-TS-002", "centre_name": "Warangal", "state": "Telangana", "district": "Warangal", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-TS-003", "centre_name": "Karimnagar", "state": "Telangana", "district": "Karimnagar", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Karnataka
        {"centre_reference_id": "ENAM-KA-001", "centre_name": "Gulbarga (Kalaburagi)", "state": "Karnataka", "district": "Kalaburagi", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-KA-002", "centre_name": "Bangalore (Yeshwantpur)", "state": "Karnataka", "district": "Bengaluru Urban", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Chhattisgarh
        {"centre_reference_id": "ENAM-CG-001", "centre_name": "Raipur", "state": "Chhattisgarh", "district": "Raipur", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-CG-002", "centre_name": "Bilaspur", "state": "Chhattisgarh", "district": "Bilaspur", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        # Andhra Pradesh
        {"centre_reference_id": "ENAM-AP-001", "centre_name": "Guntur", "state": "Andhra Pradesh", "district": "Guntur", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
        {"centre_reference_id": "ENAM-AP-002", "centre_name": "Kurnool", "state": "Andhra Pradesh", "district": "Kurnool", "source_platform": "eNAM", "source_url": "https://enam.gov.in", "data_type": "MANDI_REFERENCE_DATA"},
    ]


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    sources = load_sources()

    print("[enam] Building eNAM mandi reference data...")

    records = get_curated_enam_reference()

    # Write CSV
    out_csv = PROCESSED_DIR / "enam_mandi_reference.csv"
    fieldnames = ["centre_reference_id", "centre_name", "state", "district", "source_platform", "source_url", "data_type"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"[enam] eNAM mandi reference saved: {out_csv} ({len(records)} records)")

    sources["enam"] = {
        "name": "eNAM Mandi Reference Data",
        "original_source": "https://enam.gov.in",
        "license": "Government Open Data License (GODL) v1.0",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "record_count": len(records),
        "data_type": "MANDI_REFERENCE_DATA",
        "pii_status": "NO_PII",
        "note": "Curated reference list of major APMC/eNAM mandis. Not real-time operational data.",
    }
    save_sources(sources)
    print("[enam] Done.")


if __name__ == "__main__":
    main()
