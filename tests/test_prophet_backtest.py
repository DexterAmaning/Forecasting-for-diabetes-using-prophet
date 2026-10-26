"""Pins the Prophet results the README reports.

The notebook fits Prophet with no seasonality and no changepoints on annual
data, so it should reduce to a straight line, and its 80% interval should
contain none of the 10 held-out values (5 series x 2 years).
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from diabetes_spending import OBESITY_CLASS, class_year_totals, forecast_linear, load_diabetes_products, to_long

prophet = pytest.importorskip("prophet")

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "DSD_MCD_RY26_P06_V20_D24_BGM.csv"
NOTEBOOK = ROOT / "notebooks" / "medicaid_diabetes_spending.ipynb"
MAJOR = ["GLP-1 / GIP-GLP-1 RA", "SGLT2 inhibitor", "Insulin", "DPP-4 inhibitor"]

# The model as configured in the notebook's forecast_prophet().
CONFIG = dict(growth="linear", yearly_seasonality=False, weekly_seasonality=False,
              daily_seasonality=False, n_changepoints=0, interval_width=0.8)


def notebook_source():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "\n".join("".join(cell["source"]) for cell in nb["cells"] if cell["cell_type"] == "code")


def fit_prophet(y, first_year, horizon):
    logging.getLogger("cmdstanpy").disabled = True
    ds = pd.to_datetime([f"{first_year + i}-01-01" for i in range(len(y))])
    model = prophet.Prophet(**CONFIG)
    model.fit(pd.DataFrame({"ds": ds, "y": y}))
    future = pd.DataFrame({"ds": pd.to_datetime([f"{first_year + len(y) + i}-01-01" for i in range(horizon)])})
    return model, model.predict(future)


@pytest.fixture(scope="module")
def series():
    totals = class_year_totals(to_long(load_diabetes_products(RAW)))
    out = {cls: totals[totals.drug_class == cls].set_index("year")["spending"].values.astype(float) for cls in MAJOR}
    out["All diabetes"] = (totals[totals.drug_class != OBESITY_CLASS]
                           .groupby("year")["spending"].sum().values.astype(float))
    return out


def test_notebook_uses_the_documented_configuration():
    source = " ".join(notebook_source().split()).replace('"', "'")
    for name, value in CONFIG.items():
        assert f"{name}={value!r}" in source


@pytest.mark.skipif(not RAW.exists(), reason="raw CMS file not downloaded")
class TestBacktest:
    def test_five_annual_series(self, series):
        assert len(series) == 5
        assert all(len(y) == 5 for y in series.values())  # 2020-2024

    def test_prophet_reduces_to_a_straight_line(self, series):
        for y in series.values():
            model, forecast = fit_prophet(y[:3], 2020, 2)
            assert len(model.changepoints) == 0
            assert not model.seasonalities
            line = forecast_linear(y[:3], 2)
            assert np.max(np.abs(forecast["yhat"].values - line) / np.abs(line)) < 0.005

    def test_80_percent_interval_contains_no_held_out_value(self, series):
        np.random.seed(42)
        inside = 0
        for y in series.values():
            _, forecast = fit_prophet(y[:3], 2020, 2)
            actual = y[3:]
            inside += int(np.sum((forecast["yhat_lower"].values <= actual) & (actual <= forecast["yhat_upper"].values)))
        assert inside == 0


def test_readme_and_notebook_report_zero_of_ten():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    printed = "".join("".join(out.get("text", "")) for cell in nb["cells"] for out in cell.get("outputs", []))
    assert "Held-out values inside Prophet's 80% interval: 0 of 10" in printed
    assert "**0 of the 10**" in (ROOT / "README.md").read_text(encoding="utf-8")
