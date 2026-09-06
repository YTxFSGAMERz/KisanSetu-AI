# KisanSetu AI — Data Pipeline Setup Guide

> **SIH Problem Statement 26032** | Ministry of Consumer Affairs, Food & Public Distribution

This guide explains how to set up and run the data acquisition pipeline that provides
real government reference data to the KisanSetu system.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | `python --version` |
| pip | Latest | `pip --version` |
| Kaggle CLI | 1.6+ | `kaggle --version` |

### Install Python pipeline dependencies

```bash
pip install -r scripts/requirements-data.txt
```

---

## API Keys & Authentication

### data.gov.in API Key (Optional — for live mandi prices only)

The batch download scripts **do not require** a data.gov.in API key.

The key is only used by `backend/app/services/agmarknet_service.py` for **live real-time price lookups** at runtime. Get a free key at:
- 👉 https://data.gov.in/apis

Set it in your `.env` file:
```
DATA_GOV_IN_API_KEY=your_key_here
```

### Kaggle Credentials (Required for Agmarknet batch download)

The large Agmarknet historical dataset is downloaded via the Kaggle CLI.

**Step 1:** Create a free account at https://www.kaggle.com

**Step 2:** Go to your profile → Settings → API → "Create New API Token"

**Step 3:** This downloads `kaggle.json`. Place it at:
- **Windows:** `C:\Users\YourName\.kaggle\kaggle.json`
- **Linux/Mac:** `~/.kaggle/kaggle.json`

**OR** set as environment variables in `.env`:
```
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key
```

> **Note:** If you cannot get a Kaggle account, run with `--skip-agmarknet`.
> The system will use embedded benchmark data from `agmarknet_service.py`.

---

## Download Commands

### Full download (recommended)

```bash
# Downloads all datasets; skips existing files
python scripts/download_all_datasets.py
```

### Skip Agmarknet (no Kaggle needed)

```bash
# Use this if you don't have Kaggle configured
python scripts/download_all_datasets.py --skip-agmarknet
```

### Force re-download everything

```bash
python scripts/download_all_datasets.py --force
```

### Individual downloads

```bash
python scripts/download_agmarknet.py    # Requires Kaggle
python scripts/download_msp.py          # No auth — UPAg + embedded
python scripts/download_fci.py          # No auth — UPAg + embedded
python scripts/download_pincodes.py     # No auth — GitHub raw
python scripts/fetch_enam_reference.py  # No auth — static curated list
```

---

## Processing Commands

Run after downloading:

```bash
python scripts/process_msp.py          # → data/processed/msp/msp_reference.csv
python scripts/process_fci.py          # → data/processed/procurement/fci_procurement_reference.csv
python scripts/process_pincodes.py     # → data/processed/centres/location_reference.csv
python scripts/process_agmarknet.py    # → data/processed/mandi_arrivals/agmarknet_clean.parquet
```

---

## Validation Commands

Validation reports are written automatically by each processing script to:
```
data/metadata/validation/
  ├── msp_validation.json
  ├── fci_validation.json
  ├── pincodes_validation.json
  └── agmarknet_validation.json
```

View a report:
```bash
python -c "import json; print(json.dumps(json.load(open('data/metadata/validation/msp_validation.json')), indent=2))"
```

---

## Simulation Commands

```bash
# Run before/after congestion simulation
python scripts/simulate_congestion.py

# With custom parameters
python scripts/simulate_congestion.py --farmers 300 --counters 6 --seed 42

# View results
cat data/processed/simulation/baseline_results.json
cat docs/CONGESTION_REDUCTION_ANALYSIS.md
```

---

## Synthetic Data Generation

```bash
# Generate reproducible demo data (seed=42 is default)
python scripts/generate_synthetic_demo_data.py --seed 42

# Dry run — preview without writing files
python scripts/generate_synthetic_demo_data.py --dry-run

# 500 synthetic farmers
python scripts/generate_synthetic_demo_data.py --farmers 500
```

Output files in `data/processed/synthetic/` (gitignored — regenerate as needed).

---

## Environment Variables Reference

Add these to your `.env` file:

```bash
# ── Data Pipeline ────────────────────────────────────────
DATA_GOV_IN_API_KEY=         # Optional: live mandi prices (agmarknet_service.py)
KAGGLE_USERNAME=             # Optional: batch Agmarknet download
KAGGLE_KEY=                  # Optional: batch Agmarknet download
DATA_DIR=data                # Data directory (default: data/)
DATA_SEED=42                 # Reproducibility seed
```

---

## Complete Pipeline (all steps)

```bash
# 1. Install deps
pip install -r scripts/requirements-data.txt

# 2. Download (skip Agmarknet if no Kaggle)
python scripts/download_all_datasets.py --skip-agmarknet

# 3. Process
python scripts/process_msp.py
python scripts/process_fci.py
python scripts/process_pincodes.py
python scripts/fetch_enam_reference.py

# 4. Generate demo data
python scripts/generate_synthetic_demo_data.py --seed 42

# 5. Simulate & report
python scripts/simulate_congestion.py

# 6. Start backend (uses congestion_engine.py automatically)
cd backend && uvicorn app.main:app --reload
```

---

## Integration with KisanSetu Backend

The congestion engine is automatically available to the backend:

```python
from app.services.congestion_engine import (
    CongestionLevel,
    compute_demand_score,
    get_rolling_avg_processing_time,
    get_slot_demand_context,
)
```

The `get_slot_demand_context()` function enriches any slot with:
- Rolling historical processing time (from real `QueueToken` records)
- FCI-based demand index (seasonal + state-level)
- Enhanced congestion score (0–100)
- Arrival timing recommendation for SMS notifications

---

## Privacy & Compliance

- ✅ No real farmer PII collected
- ✅ No Aadhaar, bank, or phone data
- ✅ No rate-limit violations or CAPTCHA bypasses
- ✅ No authenticated/restricted API access
- ✅ All simulation results clearly labeled
- ✅ Synthetic data uses only fictional identifiers
