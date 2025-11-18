import math
import pandas as pd
from data_access import get_case_table

def A15F_outputs(stored_values, data):
    """
    Calculates outputs for case A15F (Rectangular Exit with Opposed Blades).
    Inputs:
    - H (in): Duct height
    - W (in): Duct width
    - N (int): Number of blades (dropdown)
    - angle (deg): Turning angle
    - Q (cfm): Flow rate

    Logic:
    - Area = H * W
    - Velocity = Q / (A / 144)
    - L/R = (N * W) / (2 * (H + W))
    - Match L/R (rounded up) to Excel col "L/R"
    - Match angle (rounded up) to Excel col "ANGLE"
    - Lookup "C" for (L/R, ANGLE)
    - Use C to compute pressure loss
    """

    H = stored_values.get("entry_1")
    W = stored_values.get("entry_2")
    N = stored_values.get("entry_3")  # Number of blades
    angle = stored_values.get("entry_4")
    Q = stored_values.get("entry_5")

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, W = {W}, N = {N}, angle = {angle}, Q = {Q}")

    if None in (H, W, N, angle, Q):
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

        perimeter = 2 * (H + W)
        L_R = (N * W) / perimeter

        print(f"[DEBUG] Area = {A:.2f} in², Velocity = {V:.2f} ft/min, L/R = {L_R:.4f}")

        df = data.loc["A15F"][["L/R", "ANGLE", "C"]].dropna()

        LR_vals = sorted(df["L/R"].unique())
        angle_vals = sorted(df["ANGLE"].unique())

        LR_match = min([val for val in LR_vals if val >= L_R], default=max(LR_vals))
        angle_match = min([val for val in angle_vals if val >= angle], default=max(angle_vals))

        print(f"[DEBUG] Matched L/R = {LR_match}, ANGLE = {angle_match}")

        matched_row = df[(df["L/R"] == LR_match) & (df["ANGLE"] == angle_match)]
        if matched_row.empty:
            return {"Error": "No matching L/R and ANGLE pair found in data."}

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
        print(f"[ERROR] Exception during A15F_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e)
        }

A15F_outputs.output_type = "standard"