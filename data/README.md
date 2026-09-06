# KisanSetu AI — Data Directory

This directory contains the government data acquisition pipeline for **SIH Problem Statement 26032**.

## ⚠️ Important Notices

- `raw/` is **gitignored** — large downloads are not committed. Run the download scripts to populate locally.
- `processed/*.csv` and `samples/*.csv` **are committed** — small reference files for reproducibility.
- `processed/*.parquet` is gitignored (large).
- `processed/synthetic/` is gitignored — regenerate with `generate_synthetic_demo_data.py`.
- **No PII is stored anywhere in this directory.**

---

## Directory Structure

```
data/
├── README.md               ← This file
│
├── raw/                    ← GITIGNORED large raw downloads
│   ├── agmarknet/          ← Agmarknet daily price CSV (from Kaggle)
│   ├── msp/                ← CACP MSP embedded JSON
│   ├── fci/                ← FCI procurement embedded JSON
│   ├── pincodes/           ← India Post pincode CSV
│   ├── enam/               ← eNAM reference (fetched directly to processed/)
│   └── crop_statistics/    ← Future: crop production statistics
│
├── processed/              ← Cleaned, normalized reference data (small files committed)
│   ├── mandi_arrivals/     ← agmarknet_clean.parquet (gitignored)
│   ├── msp/                ← msp_reference.csv ✅
│   ├── centres/            ← location_reference.csv, enam_mandi_reference.csv ✅
│   ├── crops/              ← Crop reference (populated by synthetic generator)
│   ├── procurement/        ← fci_procurement_reference.csv, demand index ✅
│   ├── simulation/         ← baseline_results.json, kisansetu_results.json ✅
│   └── synthetic/          ← GITIGNORED synthetic demo data
│
├── metadata/
│   ├── dataset_registry.json   ← Dataset provenance & license registry ✅
│   ├── sources.json            ← Download timestamps (populated at runtime) ✅
│   └── validation/             ← Data quality reports per dataset ✅
│
└── samples/                ← Small committed samples (≤100 rows) ✅
    ├── agmarknet_sample.csv
    └── msp_sample.csv
```

---

## Quick Start

```bash
# Step 1: Install pipeline dependencies
pip install -r scripts/requirements-data.txt

# Step 2: Download datasets (see DATA_SETUP.md for Kaggle setup)
python scripts/download_all_datasets.py --skip-agmarknet   # skip large file initially

# Step 3: Process all datasets
python scripts/process_msp.py
python scripts/process_fci.py
python scripts/process_pincodes.py
python scripts/fetch_enam_reference.py

# Step 4: Generate synthetic demo data
python scripts/generate_synthetic_demo_data.py --seed 42

# Step 5: Run congestion simulation
python scripts/simulate_congestion.py
```

---

## Data Sources

| Dataset | Source | License | Auth Required |
|---------|--------|---------|---------------|
| Agmarknet prices | agmarknet.gov.in via Kaggle | GODL v1.0 | Free Kaggle account |
| MSP Tables | cacp.dacnet.nic.in / upag.gov.in | GODL v1.0 | None |
| FCI Procurement | fci.gov.in / upag.gov.in | GODL v1.0 | None |
| India Pincodes | India Post via GitHub mirror | GODL compatible | None |
| eNAM Reference | enam.gov.in | GODL v1.0 | None |

---

## Privacy & Compliance

- ✅ No real farmer PII collected or stored
- ✅ No Aadhaar numbers, bank details, or phone numbers
- ✅ No authenticated/private API access
- ✅ All data is aggregate public government data
- ✅ Synthetic demo data uses fictional names only
- ✅ Simulation results clearly labeled "SIMULATION RESULTS"
