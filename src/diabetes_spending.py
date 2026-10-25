"""Helpers for analysing Medicaid spending on diabetes medicines.

Input is the CMS "Medicaid Spending by Drug" public use file (one row per
brand/generic/manufacturer, wide by year). All dollar figures are gross
spending before manufacturer rebates.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

# Brands whose FDA label is chronic weight management, not type 2 diabetes.
# They share molecules with diabetes products (semaglutide, liraglutide,
# tirzepatide) so they are tracked separately and excluded from diabetes totals.
OBESITY_LABELED_BRANDS = {"wegovy", "saxenda", "zepbound"}

OBESITY_CLASS = "Incretin (obesity-labeled)"

DIABETES_CLASSES = [
    "GLP-1 / GIP-GLP-1 RA",
    "SGLT2 inhibitor",
    "Insulin",
    "DPP-4 inhibitor",
    "Fixed-dose combination",
    "Metformin",
    "Sulfonylurea",
    "Thiazolidinedione",
    "Other (meglitinide, AGI, amylin)",
]

_MONO_PATTERNS = [
    ("GLP-1 / GIP-GLP-1 RA", r"semaglutide|dulaglutide|liraglutide|exenatide|lixisenatide|tirzepatide|albiglutide"),
    ("SGLT2 inhibitor", r"gliflozin"),
    ("DPP-4 inhibitor", r"gliptin"),
    ("Metformin", r"metformin"),
    ("Sulfonylurea", r"glipizide|glimepiride|glyburide|tolbutamide|chlorpropamide|tolazamide"),
    ("Thiazolidinedione", r"pioglitazone|rosiglitazone"),
    ("Other (meglitinide, AGI, amylin)", r"repaglinide|nateglinide|acarbose|miglitol|pramlintide"),
]

_ANY_ANTIDIABETIC = "|".join(p for _, p in _MONO_PATTERNS)

METRICS = {"Tot_Spndng": "spending", "Tot_Clms": "claims", "Tot_Dsg_Unts": "dosage_units"}


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(brand: str, generic: str) -> str | None:
    """Return the therapeutic class for a product, or None if not a diabetes medicine."""
    b = str(brand).strip().lower()
    g = str(generic).strip().lower()

    if "supplies" in g:
        return None
    is_insulin = g.startswith("insulin")
    is_antidiabetic = is_insulin or re.search(_ANY_ANTIDIABETIC, g) is not None
    if not is_antidiabetic:
        return None
    if b in OBESITY_LABELED_BRANDS:
        return OBESITY_CLASS
    if is_insulin:
        # Premixed insulins (e.g. "Insulin Lispro Protamin/Lispro") stay insulin;
        # insulin + GLP-1 products (Soliqua, Xultophy) are combinations.
        return "Fixed-dose combination" if re.search(_MONO_PATTERNS[0][1], g) else "Insulin"
    if "/" in g:
        return "Fixed-dose combination"
    for cls, pattern in _MONO_PATTERNS:
        if re.search(pattern, g):
            return cls
    return None


def years_in(df: pd.DataFrame) -> list[int]:
    return sorted(int(c[-4:]) for c in df.columns if re.fullmatch(r"Tot_Spndng_\d{4}", c))


def load_diabetes_products(path: str | Path) -> pd.DataFrame:
    """Load the CMS file, keep national 'Overall' rows and tag diabetes classes."""
    df = pd.read_csv(path)
    overall = df[df["Mftr_Name"] == "Overall"].copy()
    overall["drug_class"] = [classify(b, g) for b, g in zip(overall["Brnd_Name"], overall["Gnrc_Name"])]
    return overall[overall["drug_class"].notna()].reset_index(drop=True)


def to_long(products: pd.DataFrame) -> pd.DataFrame:
    """Reshape wide year columns to one row per product-year.

    A blank value means the product had no reported Medicaid spending that
    year (e.g. not yet launched); it is kept as NaN here and treated as zero
    only when aggregating.
    """
    frames = []
    for year in years_in(products):
        cols = {f"{prefix}_{year}": name for prefix, name in METRICS.items()}
        part = products[["Brnd_Name", "Gnrc_Name", "drug_class", *cols]].rename(columns=cols)
        part.insert(3, "year", year)
        frames.append(part)
    long = pd.concat(frames, ignore_index=True)
    return long.sort_values(["drug_class", "Brnd_Name", "Gnrc_Name", "year"]).reset_index(drop=True)


def class_year_totals(long: pd.DataFrame) -> pd.DataFrame:
    """Spending, claims and spend per claim by class and year (NaN counted as 0)."""
    totals = long.groupby(["drug_class", "year"], as_index=False)[["spending", "claims"]].sum(min_count=1).fillna(0)
    totals["spend_per_claim"] = totals["spending"] / totals["claims"].replace(0, np.nan)
    return totals


def cagr(first: float, last: float, periods: int) -> float:
    if first <= 0 or periods <= 0:
        return float("nan")
    return (last / first) ** (1 / periods) - 1


def decompose_growth(spend0: float, spend1: float, claims0: float, claims1: float) -> dict[str, float]:
    """Split log spending growth into claim volume and spend-per-claim parts.

    ln(S1/S0) = ln(C1/C0) + ln(SPC1/SPC0), so the two log parts sum to the
    total and the two shares sum to 1. Shares are unstable when total growth
    is near zero, so prefer the log parts for flat classes.
    """
    total = float(np.log(spend1 / spend0))
    volume = float(np.log(claims1 / claims0))
    price = total - volume
    return {
        "log_growth": total,
        "volume_log": volume,
        "spend_per_claim_log": price,
        "volume_share": volume / total if total else float("nan"),
        "spend_per_claim_share": price / total if total else float("nan"),
    }


# --- Simple forecasting baselines (annual series, horizon h = 1..H) ---------

def forecast_naive(y: np.ndarray, horizon: int) -> np.ndarray:
    return np.repeat(float(y[-1]), horizon)


def forecast_drift(y: np.ndarray, horizon: int) -> np.ndarray:
    slope = (y[-1] - y[0]) / (len(y) - 1)
    return y[-1] + slope * np.arange(1, horizon + 1)


def forecast_linear(y: np.ndarray, horizon: int) -> np.ndarray:
    t = np.arange(len(y))
    slope, intercept = np.polyfit(t, y, 1)
    return intercept + slope * np.arange(len(y), len(y) + horizon)


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(np.mean(np.abs((actual - predicted) / actual)) * 100)
