# case_registry.py

CASE_CONFIG = {
    # 1D example: A15C (h/D -> C)
    "A15C": {
        "sheet_key": "A15C",
        "arg_cols": ["h/D"],
        "value_col": "C",
        "excel_range": "Sheet A15C!B4:C15",  # update to real range
        "description": "Exit: Segmental opening in round duct",
    },

    # 2D example: A13C (ANGLE, As/A -> C)
    "A13C": {
        "sheet_key": "A13C",
        "arg_cols": ["ANGLE", "As/A"],
        "value_col": "C",
        "excel_range": "Sheet A13C!B4:H20",
        "description": "Rectangular conical exit with/without wall",
    },

    # 3D example: A11V branch path
    "A11V_branch": {
        "sheet_key": "A11V",
        "row_filter": {"PATH": "branch"},
        "arg_cols": ["Ab/As", "Ab/Ac", "Qb/Qc"],
        "value_col": "C",
        "excel_range": "Sheet A11V!B4:H40",
        "description": "A11V branch path loss coefficient",
    },

    # 3D example: A11V main path
    "A11V_main": {
        "sheet_key": "A11V",
        "row_filter": {"PATH": "main"},
        "arg_cols": ["Ab/As", "Ab/Ac", "Qb/Qc"],
        "value_col": "C",
        "excel_range": "Sheet A11V!B4:H40",
        "description": "A11V main path loss coefficient",
    },
}
