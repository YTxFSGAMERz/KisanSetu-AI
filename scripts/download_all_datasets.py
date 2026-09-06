"""
KisanSetu AI — Master Dataset Downloader
==========================================
Orchestrates all dataset downloads in the correct order.
Checks for existing files before re-downloading.
Records all results to data/metadata/sources.json.

Sources (all free, no paid/authenticated access):
  1. Agmarknet → Kaggle mirror (no API key required)
  2. MSP       → UPAg portal + embedded CACP reference
  3. FCI       → UPAg portal + embedded FCI reference
  4. Pincodes  → GitHub public mirror of India Post data
  5. eNAM      → Curated public reference list

Usage:
  python scripts/download_all_datasets.py
  python scripts/download_all_datasets.py --skip-agmarknet   # skip large download
  python scripts/download_all_datasets.py --force            # force re-download all
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
META_DIR = REPO_ROOT / "data" / "metadata"
SOURCES_FILE = META_DIR / "sources.json"

# ─── Import individual downloaders ───────────────────────────────────────────
# We run them as subprocess calls to isolate failures
import subprocess


def run_script(script: str, extra_args: list[str] = None) -> bool:
    """Run a downloader script, return True on success."""
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / script)]
    if extra_args:
        cmd.extend(extra_args)

    print(f"\n{'='*60}")
    print(f"Running: {script}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return result.returncode == 0


def load_sources() -> dict:
    if SOURCES_FILE.exists():
        with open(SOURCES_FILE) as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(description="KisanSetu AI — Download all datasets")
    parser.add_argument("--skip-agmarknet", action="store_true",
                        help="Skip Agmarknet (large file, requires Kaggle CLI config)")
    parser.add_argument("--force", action="store_true",
                        help="Force re-download all datasets")
    args = parser.parse_args()

    META_DIR.mkdir(parents=True, exist_ok=True)

    start = datetime.now(timezone.utc)
    print(f"\n🌾 KisanSetu AI — Data Acquisition Pipeline")
    print(f"   Started: {start.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   Repository: {REPO_ROOT}")

    results = {}

    # ── Dataset 1: Agmarknet (Kaggle) ────────────────────────────────────────
    if not args.skip_agmarknet:
        ok = run_script("download_agmarknet.py", ["--force"] if args.force else [])
        results["agmarknet"] = "SUCCESS" if ok else "FAILED"
    else:
        print("\n[orchestrator] Skipping Agmarknet download (--skip-agmarknet flag).")
        results["agmarknet"] = "SKIPPED"

    # ── Dataset 2: MSP (UPAg + embedded CACP) ────────────────────────────────
    ok = run_script("download_msp.py")
    results["msp"] = "SUCCESS" if ok else "FAILED"

    # ── Dataset 3: FCI (UPAg + embedded) ─────────────────────────────────────
    ok = run_script("download_fci.py")
    results["fci"] = "SUCCESS" if ok else "FAILED"

    # ── Dataset 4: Pincodes (GitHub) ──────────────────────────────────────────
    ok = run_script("download_pincodes.py")
    results["pincodes"] = "SUCCESS" if ok else "FAILED"

    # ── Dataset 5: eNAM Reference ─────────────────────────────────────────────
    ok = run_script("fetch_enam_reference.py")
    results["enam"] = "SUCCESS" if ok else "FAILED"

    # ── Summary ───────────────────────────────────────────────────────────────
    end = datetime.now(timezone.utc)
    elapsed = (end - start).total_seconds()

    print(f"\n{'='*60}")
    print(f"📊 Download Summary")
    print(f"{'='*60}")
    for dataset, status in results.items():
        icon = "✅" if status == "SUCCESS" else ("⏭️" if status == "SKIPPED" else "❌")
        print(f"  {icon} {dataset:<20} {status}")

    print(f"\n  ⏱  Total time: {elapsed:.1f}s")
    print(f"\n📂 Next steps:")
    print(f"  python scripts/process_agmarknet.py    # (if Agmarknet downloaded)")
    print(f"  python scripts/process_msp.py")
    print(f"  python scripts/process_fci.py")
    print(f"  python scripts/process_pincodes.py")
    print(f"  python scripts/generate_synthetic_demo_data.py")
    print(f"  python scripts/simulate_congestion.py")

    # Save run record
    sources = load_sources()
    sources["_last_run"] = {
        "timestamp": end.isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "results": results,
    }
    with open(SOURCES_FILE, "w") as f:
        json.dump(sources, f, indent=2)

    failed = [k for k, v in results.items() if v == "FAILED"]
    if failed:
        print(f"\n⚠️  Some downloads failed: {failed}")
        print("   Check logs above. Processing scripts will use embedded fallback data.")
        sys.exit(1)


if __name__ == "__main__":
    main()
