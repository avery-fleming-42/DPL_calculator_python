import math
import pandas as pd
from data_access import get_case_table

def A15C_outputs(stored_values, data):
    """
    Calculates outputs for A15C (Exit: Segmental Opening in Round Duct).
    Inputs:
    - D (in): Diameter of round duct
    - h (in): Segment height
    - Q (cfm): Flow rate

    Logic:
    - Calculate area from D
    - Calculate velocity from Q and area
    - Calculate h/D ratio
    - Round h/D down to find match in column "h/D"
    - Return corresponding "C" from Excel for loss coefficient
    """

    D = stored_values.get("entry_1")
    h = stored_values.get("entry_2")
    Q = stored_values.get("entry_3")

    print("[DEBUG] Inputs:")
    print(f"  D = {D}, h = {h}, Q = {Q}")

    if None in (D, h, Q):
        print("[DEBUG] Missing required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None
        }

    try:
        A = math.pi * (D / 2) ** 2  # in²
        V = Q / (A / 144)  # ft/min
        vp = (V / 4005) ** 2

        h_D = h / D
        print(f"[DEBUG] A = {A:.2f}, V = {V:.2f}, h/D = {h_D:.4f}")

        df = data.loc["A15C"][["h/D", "C"]].dropna()
        hD_vals = sorted(df["h/D"].unique())
        hD_match = max([val for val in hD_vals if val <= h_D], default=min(hD_vals))

        matched_row = df[df["h/D"] == hD_match]
        if matched_row.empty:
            return {"Error": "No matching h/D value found in data."}

        C = matched_row["C"].values[0]
        pressure_loss = C * vp

        print(f"[DEBUG] Matched h/D = {hD_match}, C = {C}, ΔP = {pressure_loss:.4f}")

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss": pressure_loss
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A15C_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e)
        }

A15C_outputs.output_type = "standard"
