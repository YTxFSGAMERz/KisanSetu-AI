"""
KisanSetu AI — Agmarknet Dataset Downloader
============================================
Downloads daily mandi price & arrival data from Kaggle public mirror of
official Agmarknet data (Ministry of Agriculture, GoI).

Source provenance:
  Original: https://agmarknet.gov.in (Ministry of Agriculture & Farmers Welfare)
  Mirror:   Kaggle — "Daily Market Prices of Commodity India" dataset
            (data traces back to official Agmarknet portal)

Usage:
  python scripts/download_agmarknet.py
  python scripts/download_agmarknet.py --skip-kaggle  # skips if file exists

Requirements:
  - kaggle CLI configured: ~/.kaggle/kaggle.json
  - OR KAGGLE_USERNAME + KAGGLE_KEY in environment
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw" / "agmarknet"
META_DIR = REPO_ROOT / "data" / "metadata"
SOURCES_FILE = META_DIR / "sources.json"

# Kaggle dataset identifier (no auth wall — public dataset)
KAGGLE_DATASET = "srinathankumar/daily-market-prices-of-commodity-india"
KAGGLE_FILE = "daily_market_prices.csv"


def load_sources() -> dict:
    if SOURCES_FILE.exists():
        with open(SOURCES_FILE) as f:
            return json.load(f)
    return {}


def save_sources(sources: dict) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    with open(SOURCES_FILE, "w") as f:
        json.dump(sources, f, indent=2)


def download_via_kaggle(dest_dir: Path, skip_if_exists: bool = True) -> bool:
    """
    Download Agmarknet daily price dataset from Kaggle.
    Returns True on success.
    """
    dest_file = dest_dir / KAGGLE_FILE
    if skip_if_exists and dest_file.exists():
        size_mb = dest_file.stat().st_size / 1_048_576
        print(f"[agmarknet] File already exists ({size_mb:.1f} MB): {dest_file}")
        print("[agmarknet] Use --force to re-download.")
        return True

    print(f"[agmarknet] Downloading dataset: {KAGGLE_DATASET}")
    print(f"[agmarknet] Destination: {dest_dir}")

    try:
        import subprocess
        result = subprocess.run(
            [
                "kaggle", "datasets", "download",
                "-d", KAGGLE_DATASET,
                "-p", str(dest_dir),
                "--unzip",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            print(f"[agmarknet] ERROR: kaggle CLI failed:\n{result.stderr}")
            return False
        print(f"[agmarknet] Download complete.\n{result.stdout}")
        return True
    except FileNotFoundError:
        print("[agmarknet] ERROR: kaggle CLI not found. Install with: pip install kaggle")
        print("[agmarknet] Then configure: https://github.com/Kaggle/kaggle-api#api-credentials")
        return False
    except Exception as e:
        print(f"[agmarknet] ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download Agmarknet dataset from Kaggle")
    parser.add_argument("--force", action="store_true", help="Force re-download even if file exists")
    parser.add_argument("--skip-kaggle", action="store_true", help="Skip download (use if manually placing file)")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sources = load_sources()

    if args.skip_kaggle:
        print("[agmarknet] --skip-kaggle flag set. Skipping download.")
        print(f"[agmarknet] Manually place your CSV as: {RAW_DIR / KAGGLE_FILE}")
        return

    success = download_via_kaggle(RAW_DIR, skip_if_exists=not args.force)

    dest_file = RAW_DIR / KAGGLE_FILE
    sources["agmarknet"] = {
        "name": "Daily Market Prices of Commodity India (Agmarknet Mirror)",
        "original_source": "https://agmarknet.gov.in",
        "mirror_source": f"https://www.kaggle.com/datasets/{KAGGLE_DATASET}",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS" if success else "FAILED",
        "local_file": str(dest_file.relative_to(REPO_ROOT)) if dest_file.exists() else None,
        "file_size_bytes": dest_file.stat().st_size if dest_file.exists() else None,
    }
    save_sources(sources)

    if not success:
        print("\n[agmarknet] Notice: Kaggle download failed or credentials not configured.")
        print("[agmarknet] Automatically falling back to generating synthetic Agmarknet dataset...")
        try:
            import subprocess
            res = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "generate_agmarknet_synthetic.py")],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                print(res.stdout)
                print("[agmarknet] Successfully generated synthetic Agmarknet fallback dataset.")
                print(f"[agmarknet] Done. File: {dest_file}")
                return
            else:
                print(f"[agmarknet] Fallback generation error:\n{res.stderr}")
        except Exception as fallback_err:
            print(f"[agmarknet] Fallback generation failed: {fallback_err}")

        print("\n[agmarknet] FALLBACK: Manual download instructions:")
        print("  1. Visit: https://www.kaggle.com/datasets/srinathankumar/daily-market-prices-of-commodity-india")
        print("  2. Click 'Download' → download the zip")
        print(f"  3. Extract and place the CSV as: {RAW_DIR / KAGGLE_FILE}")
        sys.exit(1)

    print(f"[agmarknet] Done. File: {dest_file}")


if __name__ == "__main__":
    main()
