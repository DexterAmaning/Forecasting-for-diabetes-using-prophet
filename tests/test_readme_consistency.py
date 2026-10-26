"""The README must report what the committed notebook actually printed.

These tests read the committed files only; they don't re-run the analysis.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
NOTEBOOK = ROOT / "notebooks" / "medicaid_diabetes_spending.ipynb"

DECIMAL = re.compile(r"(?<![\w.])-?\d+\.\d+(?![\w])")


def notebook_text():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    parts = []
    for cell in nb["cells"]:
        parts.append("".join(cell["source"]))
        for out in cell.get("outputs", []):
            parts.append("".join(out.get("text", "")))
            parts.append("".join(out.get("data", {}).get("text/plain", "")))
    return "\n".join(parts).replace(",", "")


def readme_decimals():
    text = README.read_text(encoding="utf-8")
    # Not results: URLs, DOIs and the tested Python version.
    text = re.sub(r"https?://\S+|10\.\d{4,}/\S+|Python \d+\.\d+", "", text)
    return sorted(set(DECIMAL.findall(text.replace(",", "").replace("−", "-"))))


def places(number):
    return len(number.split(".")[1])


def is_rounding_of(reported, printed):
    """True if `reported` can be a rounding of the value behind `printed`."""
    if places(printed) < places(reported):
        return False
    slack = 0.5 * 10 ** -places(reported) + 0.5 * 10 ** -places(printed)
    return abs(float(printed) - float(reported)) <= slack + 1e-12


def test_every_readme_decimal_is_a_rounding_of_a_notebook_value():
    printed = set(DECIMAL.findall(notebook_text()))
    missing = []
    for number in readme_decimals():
        as_fraction = f"{float(number) / 100:.{places(number) + 2}f}"  # 24.3 (%) -> 0.243
        if not any(is_rounding_of(n, p) for n in (number, as_fraction) for p in printed):
            missing.append(number)
    assert not missing, f"README numbers not found in the notebook outputs: {missing}"


def test_rounding_check_rejects_a_wrong_value():
    assert is_rounding_of("3.17", "3.175")
    assert is_rounding_of("0.90", "0.895")
    assert not is_rounding_of("3.19", "3.175")
    assert not is_rounding_of("2.40", "2.375")


def test_notebook_ran_top_to_bottom_without_errors():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
    assert [cell["execution_count"] for cell in code] == list(range(1, len(code) + 1))
    outputs = [out for cell in code for out in cell.get("outputs", [])]
    assert not [out for out in outputs if out.get("output_type") == "error"]
    assert not [out for out in outputs if "Traceback" in "".join(out.get("text", ""))]


def test_readme_links_and_figures_exist():
    text = README.read_text(encoding="utf-8")
    targets = re.findall(r"\]\(([^)#\s]+)\)", text)
    local = [t for t in targets if not re.match(r"[a-z]+://", t)]
    assert local, "expected the README to link the notebook and figures"
    assert not [t for t in local if not (ROOT / t).exists()]
