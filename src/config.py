from pathlib import Path
import sys
import os

# Repo root: one level up from src/
ROOT_DIR = Path(__file__).resolve().parents[1]

SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
FIGURES_DIR = ROOT_DIR / "duct_figures"

# Excel file path (normal run)
EXCEL_FILE_PATH = DATA_DIR / "DPL_data.xlsx"

def get_data_file_path(filename: str) -> str:
    """
    Returns the path to a data file (e.g., DPL_data.xlsx).
    Handles PyInstaller (_MEIPASS) and normal script mode.
    """
    if hasattr(sys, "_MEIPASS"):
        # inside PyInstaller bundle
        return os.path.join(sys._MEIPASS, filename)
    else:
        return str(DATA_DIR / filename)

