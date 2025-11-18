import math
import pandas as pd
from data_access import get_case_table


def A14B2_outputs(stored_values, data):
    """
    Calculates the outputs for A14B2 (rectangular perforated plate).
    Inputs: H, W, Q, n, plate thickness, perforated hole diameter.
    Logic:
    - Calculates velocity from H and W.
    - Computes t/D from plate thickness and hole diameter.
    - Matches t/D (round down) and n (round down) to find loss coefficient C from A14B2.
    """

    H = stored_values.get("entry_1")
    W = stored_values.get("entry_2")
    Q = stored_values.get("entry_3")
    n = stored_values.get("entry_4")
    t = stored_values.get("entry_5")  # Plate thickness
    d_hole = stored_values.get("entry_6")  # Hole diameter

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, W = {W}, Q = {Q}, n = {n}, t = {t}, d_hole = {d_hole}")

    if None in (H, W, Q, n, t, d_hole):
        print("[DEBUG] Missing one or more required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = H * W  # in^2
        V = Q / (A / 144)  # ft/min
        t_D = t / d_hole

        print(f"[DEBUG] Area = {A:.2f} in^2, Velocity = {V:.2f} ft/min, t/D = {t_D:.4f}")

        df = data.loc["A14B2"]
        df = df[["n, free area ratio", "t/D", "C"]].dropna()

        n_vals = df["n, free area ratio"].unique()
        tD_vals = df["t/D"].unique()

        n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
        tD_match = max([val for val in tD_vals if val <= t_D], default=min(tD_vals))

        print(f"[DEBUG] Matching n = {n_match}, t/D = {tD_match}")

        matched_row = df[(df["n, free area ratio"] == n_match) & (df["t/D"] == tD_match)]
        if matched_row.empty:
            print("[DEBUG] No match found in A14B2 table.")
            return {"Error": "No matching entry in A14B2 table."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Loss Coefficient C = {C}")

        vp = (V / 4005) ** 2
        pressure_loss = C * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A14B2_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }


A14B2_outputs.output_type = "standard"
