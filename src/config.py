from pathlib import Path
import os
import sys

# Root of the repo (folder that contains src/, data/, etc.)
ROOT_DIR = Path(__file__).resolve().parents[1]

SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
FIGURES_DIR = ROOT_DIR / "duct_figures"

# Excel file path
EXCEL_FILE_PATH = DATA_DIR / "DPL_data.xlsx"


def get_data_file_path(filename: str) -> str:
    """
    Return the path to a data file (e.g. DPL_data.xlsx).
    Handles both normal Python and PyInstaller builds.
    """
    if hasattr(sys, "_MEIPASS"):
        # When running from a PyInstaller bundle
        return os.path.join(sys._MEIPASS, filename)
    return str(DATA_DIR / filename)
