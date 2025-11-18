import math
import pandas as pd
from data_access import get_case_table

def A13C_outputs(stored_values, data):
    """
    A13C: Rectangular Conical Exit with or without Wall
    Inputs: H, H_s, W, angle (deg), Q (cfm), obstruction, optional n (if screen)
    """
    H = stored_values.get("entry_1")  # height (in)
    Hs = stored_values.get("entry_2")  # exit height (in)
    W = stored_values.get("entry_3")  # width (in)
    angle = stored_values.get("entry_4")  # degrees
    Q = stored_values.get("entry_5")  # flow rate
    obstruction = stored_values.get("entry_6")  # none or screen
    n = stored_values.get("entry_7")  # free area ratio if screen

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, Hs = {Hs}, W = {W}, angle = {angle}, Q = {Q}, obstruction = {obstruction}, n = {n}")

    if None in (H, Hs, W, angle, Q):
        print("[DEBUG] Missing required inputs")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = H * W
        As = Hs * W
        A_ratio = As / A
        V = Q / (A / 144)  # ft/min
        vp = (V / 4005) ** 2

        df = data.loc["A13C"]
        df = df[["ANGLE", "As/A", "C"]].dropna()

        # Round angle up
        angle_vals = df["ANGLE"].unique()
        angle_match = min([val for val in angle_vals if val >= angle], default=max(angle_vals))

        # Area ratio rounding
        ratio_vals = df[df["ANGLE"] == angle_match]["As/A"].unique()
        if angle <= 20:
            ratio_match = max([val for val in ratio_vals if val <= A_ratio], default=min(ratio_vals))
        else:
            ratio_match = min(ratio_vals, key=lambda x: abs(x - A_ratio))

        matched_row = df[(df["ANGLE"] == angle_match) & (df["As/A"] == ratio_match)]
        if matched_row.empty:
            return {"Error": "No matching data in A13C for given angle and area ratio."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        # Obstruction correction
        C1 = 0
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen C1 = {C1}")

        if obstruction == "screen":
            loss_coefficient = C + (C1 / (As / A) ** 2)
            print("[DEBUG] Applying screen correction")
        else:
            loss_coefficient = C

        total_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": total_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception in A13C_outputs: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A13C_outputs.output_type = "standard"