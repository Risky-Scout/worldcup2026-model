"""
Instructions for downloading the Kaggle international football results dataset.

Dataset: "International football results from 1872 to 2024"
URL: https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017

This script prints download instructions. The dataset cannot be downloaded
automatically without Kaggle API credentials.
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    target = Path(__file__).resolve().parents[1] / "data" / "external" / "international_results.csv"

    print(
        "\n=== Download International Football Results (Kaggle) ===\n"
        "\nDataset: International football results from 1872 to 2026"
        "\nURL: https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017\n"
        "\nMethod 1 — Kaggle CLI (recommended):"
        "\n  pip install kaggle"
        "\n  kaggle datasets download -d martj42/international-football-results-from-1872-to-2017"
        f"\n  mv results.csv {target}\n"
        "\nMethod 2 — Manual download:"
        "\n  1. Visit the URL above and download results.csv"
        f"\n  2. Save as: {target}\n"
        "\nThe file is expected at:"
        f"\n  {target}\n"
        "\nOnce downloaded, the international_poisson.py module will automatically"
        "\nblend per-team offensive/defensive abilities at 15% weight into the"
        "\nCompositeTeamPrior when CompositeTeamPrior.fit() is called.\n"
    )

    if target.exists():
        import pandas as pd
        df = pd.read_csv(target, nrows=5)
        print(f"File already exists: {target}")
        print(f"Shape (rows estimated): check full file. Preview:\n{df}\n")
    else:
        print(f"File NOT found at: {target}")
        print("Please follow the download instructions above.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
