import math
import pandas as pd
from data_access import get_case_table

def A15D_outputs(stored_values, data):
    """
    Calculates outputs for case A15D (Rectangular Duct with Segmental Exit).
    Inputs:
    - H (in): Duct height
    - W (in): Duct width
    - h (in): Exit segment height
    - Q (cfm): Flow rate

    Logic:
    - Calculate area from H and W
    - Calculate velocity and velocity pressure
    - Calculate H/W and h/H
    - Match H/W to nearest in Excel column "H/W"
    - Match h/H to floor in Excel column "h/H"
    - Use both to find corresponding "C"
    """

    H = stored_values.get("entry_1")
    W = stored_values.get("entry_2")
    h = stored_values.get("entry_3")
    Q = stored_values.get("entry_4")

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, W = {W}, h = {h}, Q = {Q}")

    if None in (H, W, h, Q):
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

        H_W = H / W
        h_H = h / H
        print(f"[DEBUG] Area = {A:.2f}, Velocity = {V:.2f}, H/W = {H_W:.3f}, h/H = {h_H:.3f}")

        # Use centralized loader instead of `data.loc[...]`
        df = get_case_table("A15D")[["H/W", "h/H", "C"]].dropna()

        # Nearest match for H/W
        HW_vals = df["H/W"].unique()
        HW_match = min(HW_vals, key=lambda x: abs(x - H_W))

        # Round down for h/H
        hH_vals = sorted(df["h/H"].unique())
        hH_match = max([val for val in hH_vals if val <= h_H], default=min(hH_vals))

        print(f"[DEBUG] Matched H/W = {HW_match}, h/H = {hH_match}")

        matched_row = df[(df["H/W"] == HW_match) & (df["h/H"] == hH_match)]
        if matched_row.empty:
            return {"Error": "No matching H/W and h/H pair found in A15D data."}

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
        print(f"[ERROR] Exception occurred during A15D_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e)
        }

A15D_outputs.output_type = "standard"
