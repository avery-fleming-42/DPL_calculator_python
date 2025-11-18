import math
import pandas as pd
from data_access import get_case_table

def A15G_outputs(stored_values, data):
    """
    Calculates outputs for case A15G (Rectangular Exit without Blades).
    Inputs:
    - H (in): Duct height
    - W (in): Duct width
    - angle (deg): Turning angle
    - Q (cfm): Flow rate

    Logic:
    - Area = H * W
    - Velocity = Q / (A / 144)
    - Match angle (rounded up) to Excel col "ANGLE"
    - Lookup "C" from A15G table
    """

    H = stored_values.get("entry_1")
    W = stored_values.get("entry_2")
    angle = stored_values.get("entry_3")
    Q = stored_values.get("entry_4")

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, W = {W}, angle = {angle}, Q = {Q}")

    if None in (H, W, angle, Q):
        print("[DEBUG] Missing required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None
        }

    try:
        A = H * W  # in²
        V = Q / (A / 144)  # ft/min
        vp = (V / 4005) ** 2

        print(f"[DEBUG] Area = {A:.2f} in², Velocity = {V:.2f} ft/min")

        df = data.loc["A15G"][["ANGLE", "C"]].dropna()
        angle_vals = sorted(df["ANGLE"].unique())
        angle_match = min([val for val in angle_vals if val >= angle], default=max(angle_vals))

        print(f"[DEBUG] Matched ANGLE = {angle_match}")

        matched_row = df[df["ANGLE"] == angle_match]
        if matched_row.empty:
            return {"Error": "No matching angle found in data."}

        C = matched_row["C"].values[0]
        pressure_loss = C * vp

        print(f"[DEBUG] C = {C}, ΔP = {pressure_loss:.4f}")

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss": pressure_loss
        }

    except Exception as e:
        print(f"[ERROR] Exception during A15G_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e)
        }

A15G_outputs.output_type = "standard"