from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


SHEET_MAP = {
    "cpus": "CPUs",
    "motherboards": "MBs",
    "rams": "RAMs",
    "storage": "Storage",
    "gpus": "GPUs",
    "psus": "PSUs",
}


def _to_records(df: pd.DataFrame) -> List[Dict]:
    """Convert a DataFrame into JSON-safe records."""
    clean_df = df.where(pd.notnull(df), None)
    return clean_df.to_dict(orient="records")


def load_components(excel_path: str | Path) -> Dict[str, List[Dict]]:
    """Load all component sheets from the Excel file."""
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    xls = pd.ExcelFile(excel_path)
    components: Dict[str, List[Dict]] = {}

    for key, sheet_name in SHEET_MAP.items():
        if sheet_name not in xls.sheet_names:
            raise ValueError(f"Missing required sheet '{sheet_name}' in {excel_path}")
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        components[key] = _to_records(df)

    return components
