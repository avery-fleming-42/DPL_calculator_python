# src/config.py
from pathlib import Path
import os
import sys

# ----------------------------
# Paths: repo root and folders
# ----------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]   # repo/
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
FIGURES_DIR = ROOT_DIR / "duct_figures"

# NEW: directory for case-specific Excel tables
CASE_TABLES_DIR = DATA_DIR / "case_tables"

# ----------------------------
# Master Excel file (inputs)
# ----------------------------
EXCEL_FILE_PATH = DATA_DIR / "DPL_data.xlsx"

# ----------------------------
# Helper functions
# ----------------------------
def get_data_file_path(filename: str) -> str:
    """
    Return absolute path to a data file in /data/.
    Supports both normal Python execution and PyInstaller builds.
    """
    if hasattr(sys, "_MEIPASS"):  # PyInstaller unpacked runtime
        return os.path.join(sys._MEIPASS, filename)
    return str(DATA_DIR / filename)


def get_figure_path(filename: str) -> str:
    """
    Return absolute path to a figure inside /duct_figures/.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "duct_figures", filename)
    return str(FIGURES_DIR / filename)


def get_case_table_path(filename: str) -> str:
    """
    Return absolute path to a per-duct case table Excel file.
    e.g. A7A_cleaned.xlsx
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "case_tables", filename)
    return str(CASE_TABLES_DIR / filename)
