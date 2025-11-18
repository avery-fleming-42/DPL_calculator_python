# src/data_access.py
import pandas as pd
from functools import lru_cache
from pathlib import Path

from config import EXCEL_FILE_PATH, get_case_table_path


@lru_cache(maxsize=None)
def load_all_sheets():
    """
    Read the entire master workbook once and cache it.
    Returns: dict {sheet_name: DataFrame}
    """
    return pd.read_excel(EXCEL_FILE_PATH, sheet_name=None)


@lru_cache(maxsize=None)
def get_case_table(duct_id: str) -> pd.DataFrame:
    """
    Return the DataFrame for a single duct case.

    Resolution order:
      1. Look for a dedicated Excel file in data/case_tables/, e.g.:
         - A7A_cleaned.xlsx
         - A7A.xlsx
      2. If no file exists, fall back to the 'Master Table' sheet
         in DPL_data.xlsx and filter by ID == duct_id.
    """
    # -----------------------------
    # 1) Try per-duct Excel files
    # -----------------------------
    filename_candidates = [
        f"{duct_id}_cleaned.xlsx",
        f"{duct_id}.xlsx",
    ]

    for fname in filename_candidates:
        path_str = get_case_table_path(fname)
        path = Path(path_str)
        if path.exists():
            df = pd.read_excel(path)
            # Drop fully empty columns just in case
            df = df.dropna(axis=1, how="all")
            return df

    # --------------------------------------------
    # 2) Fallback: use the master workbook's data
    # --------------------------------------------
    sheets = load_all_sheets()

    master = sheets.get("Master Table")
    if master is None:
        raise KeyError("No 'Master Table' sheet found in workbook.")

    if "ID" not in master.columns:
        raise KeyError("'Master Table' is missing 'ID' column.")

    case_df = master[master["ID"] == duct_id]
    if case_df.empty:
        raise KeyError(f"Duct ID '{duct_id}' not found in Master Table and no per-case file found.")

    return case_df.dropna(axis=1, how="all")
