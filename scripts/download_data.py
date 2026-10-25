"""Download the CMS Medicaid Spending by Drug file used in this analysis and verify it.

Usage:  python scripts/download_data.py

The file is committed to the repository already; this script documents where
it came from and lets you re-download and verify it. CMS publishes a new
release every year at a new URL; a newer release will fail the checksum by
design, because the notebook's results are tied to this exact file.
"""

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from diabetes_spending import sha256  # noqa: E402

URL = (
    "https://data.cms.gov/sites/default/files/2026-06/"
    "ae1c5e06-957d-42dd-b783-e7fe598c01c9/DSD_MCD_RY26_P06_V20_D24_BGM.csv"
)
EXPECTED_SHA256 = "29294c174ee7ad6cbe97008b85af3f2887ff2600e6bb95503064fd5f27ae6624"
DEST = Path(__file__).resolve().parents[1] / "data" / "raw" / "DSD_MCD_RY26_P06_V20_D24_BGM.csv"


def main() -> int:
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if not DEST.exists():
        print(f"Downloading {URL}")
        urllib.request.urlretrieve(URL, DEST)
    digest = sha256(DEST)
    if digest != EXPECTED_SHA256:
        print(f"Checksum mismatch: {digest}\nexpected        {EXPECTED_SHA256}")
        return 1
    print(f"OK: {DEST.name} matches the documented release")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
