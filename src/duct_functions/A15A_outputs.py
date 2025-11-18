import math
import pandas as pd
from data_access import get_case_table

def A15A_outputs(stored_values, data):
    """
    Calculates outputs for A15A (Exit: Elliptical Opening at End of Duct).
    Inputs:
    - D (in): Duct diameter
    - Q (cfm): Flow rate
    - angle (deg): Elliptical opening angle

    Logic:
    - Compute area from D
    - Compute velocity from Q and A
    - Round up angle to find matching "C" value from A15A table using column "ANGLE"
    """

    D = stored_values.get("entry_1")
    Q = stored_values.get("entry_2")
    angle = stored_values.get("entry_3")

    print("[DEBUG] Inputs:")
    print(f"  D = {D}, Q = {Q}, angle = {angle}")

    if None in (D, Q, angle):
        print("[DEBUG] Missing required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None
        }

    try:
        # Area and velocity
        A = math.pi * (D / 2) ** 2        # in²
        V = Q / (A / 144)                 # ft/min
        vp = (V / 4005) ** 2

        # Pull A15A table via get_case_table (ignore `data` arg)
        df = get_case_table("A15A")[["ANGLE", "C"]].dropna()

        # Match angle to data table (round up)
        angle_vals = sorted(df["ANGLE"].unique())
        angle_match = min([val for val in angle_vals if val >= angle], default=max(angle_vals))

        matched_row = df[df["ANGLE"] == angle_match]
        if matched_row.empty:
            return {"Error": "No matching angle found in A15A data."}

        C = matched_row["C"].values[0]
        pressure_loss = C * vp

        print(f"[DEBUG] A = {A:.2f}, V = {V:.2f}, vp = {vp:.4f}, "
              f"C = {C}, ΔP = {pressure_loss:.4f}")

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss": pressure_loss
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A15A_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e)
        }

A15A_outputs.output_type = "standard"
