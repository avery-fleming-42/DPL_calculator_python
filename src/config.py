from pathlib import Path
import os

# Base directory: repo root (one level above src/)
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
CASE_TABLES_DIR = DATA_DIR / "case_tables"
FIGURES_DIR = BASE_DIR / "duct_figures"

_DEFAULT_EXCEL_NAME = "DPL_data.xlsx" # or "DPL_data.xlsx" – see next section

def get_data_file_path(name: str) -> Path:
    return DATA_DIR / name

def get_case_table_path(name: str) -> Path:
    return CASE_TABLES_DIR / name

EXCEL_FILE_PATH = Path(
    os.environ.get("DUCT_EXCEL_PATH", str(get_data_file_path(_DEFAULT_EXCEL_NAME)))
).expanduser().resolve()
