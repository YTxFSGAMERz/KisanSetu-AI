"""
KisanSetu AI — India Pincode Reference Downloader
===================================================
Downloads the India pincode directory (post office / district / state mapping)
from public GitHub mirror of official India Post data.

Source provenance:
  Original: India Post (Department of Posts, Ministry of Communications, GoI)
  Mirror:   https://github.com/dropdevrahul/pincodes-india (public, no auth)
  License:  Government Open Data License (GODL) compatible

Use in KisanSetu:
  - Generate realistic procurement centre seed locations
  - Validate farmer-registered districts
  - Simulate realistic geographic distribution of farmers

No personal addresses are collected — only post office level geographic data.

Usage:
  python scripts/download_pincodes.py
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw" / "pincodes"
META_DIR = REPO_ROOT / "data" / "metadata"
SOURCES_FILE = META_DIR / "sources.json"

TIMEOUT = 30
HEADERS = {"User-Agent": "KisanSetu-AI Research Pipeline / SIH 26032"}

# Direct raw CSV URL — GitHub public repository, no auth required
PINCODE_URL = (
    "https://raw.githubusercontent.com/dropdevrahul/pincodes-india/master/pincode.csv"
)


def load_sources() -> dict:
    if SOURCES_FILE.exists():
        with open(SOURCES_FILE) as f:
            return json.load(f)
    return {}


def save_sources(sources: dict):
    META_DIR.mkdir(parents=True, exist_ok=True)
    with open(SOURCES_FILE, "w") as f:
        json.dump(sources, f, indent=2)


def download_pincodes(dest_dir: Path, skip_if_exists: bool = True) -> bool:
    dest_file = dest_dir / "pincode.csv"
    if skip_if_exists and dest_file.exists():
        size_mb = dest_file.stat().st_size / 1_048_576
        print(f"[pincodes] File already exists ({size_mb:.1f} MB): {dest_file}")
        return True

    print(f"[pincodes] Downloading from: {PINCODE_URL}")
    try:
        r = requests.get(PINCODE_URL, headers=HEADERS, timeout=TIMEOUT, stream=True)
        r.raise_for_status()
        with open(dest_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        size_mb = dest_file.stat().st_size / 1_048_576
        print(f"[pincodes] Downloaded: {dest_file} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"[pincodes] Download failed: {e}")
        return False


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sources = load_sources()

    success = download_pincodes(RAW_DIR)
    dest_file = RAW_DIR / "pincode.csv"

    sources["pincodes"] = {
        "name": "India Pincode Directory (Post Office / District / State)",
        "original_source": "India Post, Department of Posts, Government of India",
        "mirror_source": "https://github.com/dropdevrahul/pincodes-india",
        "mirror_url": PINCODE_URL,
        "license": "Government Open Data License (GODL) compatible",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS" if success else "FAILED",
        "local_file": str(dest_file.relative_to(REPO_ROOT)) if dest_file.exists() else None,
        "file_size_bytes": dest_file.stat().st_size if dest_file.exists() else None,
        "pii_note": "Post office level only — no individual addresses",
    }
    save_sources(sources)

    if not success:
        print("[pincodes] Manual fallback: Download from https://github.com/dropdevrahul/pincodes-india")
        print(f"[pincodes] Place as: {RAW_DIR / 'pincode.csv'}")
    else:
        print("[pincodes] Done.")


if __name__ == "__main__":
    main()
