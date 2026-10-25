# Data

## `raw/DSD_MCD_RY26_P06_V20_D24_BGM.csv`

| | |
|---|---|
| Dataset | Medicaid Spending by Drug |
| Publisher | Centers for Medicare & Medicaid Services (CMS) |
| Release | Data year 2024 (covers 2020–2024), published June 2026 |
| Landing page | https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-spending-by-drug/medicaid-spending-by-drug |
| Direct file | https://data.cms.gov/sites/default/files/2026-06/ae1c5e06-957d-42dd-b783-e7fe598c01c9/DSD_MCD_RY26_P06_V20_D24_BGM.csv |
| Downloaded | 2026-10-24 |
| SHA-256 | `29294c174ee7ad6cbe97008b85af3f2887ff2600e6bb95503064fd5f27ae6624` |
| Size | 18,511 rows × 36 columns |
| Access | Public (`accessLevel: public` in the data.cms.gov catalog) |
| License | U.S. federal government work, public domain in the U.S.; redistributed here unchanged |

One row per brand name / generic name / manufacturer. Rows with `Mftr_Name == "Overall"` are the national brand totals used in the analysis. Spending is **gross, before manufacturer rebates**. CMS documentation lists further methodological notes.

To re-download and verify: `python scripts/download_data.py`.

This dataset contains aggregate national drug-level totals only. It has no patient-level or identifiable information.
