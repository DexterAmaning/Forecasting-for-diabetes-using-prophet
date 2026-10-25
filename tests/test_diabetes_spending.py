from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from diabetes_spending import (
    OBESITY_CLASS,
    class_year_totals,
    classify,
    decompose_growth,
    forecast_drift,
    forecast_linear,
    forecast_naive,
    load_diabetes_products,
    mape,
    sha256,
    to_long,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "DSD_MCD_RY26_P06_V20_D24_BGM.csv"
EXPECTED_SHA256 = "29294c174ee7ad6cbe97008b85af3f2887ff2600e6bb95503064fd5f27ae6624"


@pytest.mark.parametrize(
    "brand, generic, expected",
    [
        ("Ozempic", "Semaglutide", "GLP-1 / GIP-GLP-1 RA"),
        ("Mounjaro", "Tirzepatide", "GLP-1 / GIP-GLP-1 RA"),
        ("Wegovy", "Semaglutide", OBESITY_CLASS),
        ("Zepbound", "Tirzepatide", OBESITY_CLASS),
        ("Saxenda", "Liraglutide", OBESITY_CLASS),
        ("Jardiance", "Empagliflozin", "SGLT2 inhibitor"),
        ("Januvia", "Sitagliptin Phosphate", "DPP-4 inhibitor"),
        ("Janumet", "Sitagliptin Phos/Metformin HCl", "Fixed-dose combination"),
        ("Humalog Mix 75-25", "Insulin Lispro Protamin/Lispro", "Insulin"),
        ("Soliqua 100-33", "Insulin Glargine/Lixisenatide", "Fixed-dose combination"),
        ("Metformin HCl", "Metformin HCl", "Metformin"),
        ("Glipizide", "Glipizide", "Sulfonylurea"),
        ("Actos", "Pioglitazone HCl", "Thiazolidinedione"),
        ("Novopen Echo", "Insulin Admin. Supplies", None),
        ("Lisinopril", "Lisinopril", None),
        ("Tylenol", "Acetaminophen", None),
    ],
)
def test_classify(brand, generic, expected):
    assert classify(brand, generic) == expected


def _toy_products():
    return pd.DataFrame(
        {
            "Brnd_Name": ["A", "B"],
            "Gnrc_Name": ["Semaglutide", "Metformin HCl"],
            "drug_class": ["GLP-1 / GIP-GLP-1 RA", "Metformin"],
            "Tot_Spndng_2020": [np.nan, 10.0],
            "Tot_Clms_2020": [np.nan, 5.0],
            "Tot_Dsg_Unts_2020": [np.nan, 50.0],
            "Tot_Spndng_2021": [100.0, 12.0],
            "Tot_Clms_2021": [2.0, 6.0],
            "Tot_Dsg_Unts_2021": [4.0, 60.0],
        }
    )


def test_to_long_shape_and_years():
    long = to_long(_toy_products())
    assert len(long) == 4
    assert sorted(long["year"].unique()) == [2020, 2021]
    assert long.loc[(long.Brnd_Name == "B") & (long.year == 2021), "spending"].item() == 12.0


def test_class_totals_treat_missing_as_zero():
    totals = class_year_totals(to_long(_toy_products()))
    glp1_2020 = totals[(totals.drug_class == "GLP-1 / GIP-GLP-1 RA") & (totals.year == 2020)]
    assert glp1_2020["spending"].item() == 0
    assert np.isnan(glp1_2020["spend_per_claim"].item())


def test_decomposition_shares_sum_to_one():
    parts = decompose_growth(100, 300, 10, 20)
    assert parts["volume_share"] + parts["spend_per_claim_share"] == pytest.approx(1.0)
    assert parts["log_growth"] == pytest.approx(np.log(3))
    assert parts["volume_log"] + parts["spend_per_claim_log"] == pytest.approx(np.log(3))


def test_forecast_baselines():
    y = np.array([10.0, 20.0, 30.0])
    assert forecast_naive(y, 2).tolist() == [30.0, 30.0]
    assert forecast_drift(y, 2).tolist() == [40.0, 50.0]
    assert forecast_linear(y, 2) == pytest.approx([40.0, 50.0])
    assert mape([100, 200], [110, 180]) == pytest.approx(10.0)


@pytest.mark.skipif(not RAW.exists(), reason="raw CMS file not downloaded")
class TestRawData:
    def test_checksum_matches_documented_release(self):
        assert sha256(RAW) == EXPECTED_SHA256

    def test_diabetes_extract(self):
        products = load_diabetes_products(RAW)
        assert not products.duplicated(["Brnd_Name", "Gnrc_Name"]).any()
        assert products["drug_class"].isin({OBESITY_CLASS}).sum() == 3
        assert "Tylenol" not in set(products["Brnd_Name"])
        long = to_long(products)
        assert sorted(long["year"].unique()) == [2020, 2021, 2022, 2023, 2024]
