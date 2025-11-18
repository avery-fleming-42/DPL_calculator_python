import math
import pandas as pd
from data_access import get_case_table


def A14A2_outputs(stored_values, data):
    """
    Calculates the outputs for case A14A2 (rectangular screen):
    - Uses duct height H and width W to compute area and velocity
    - Uses n to look up loss coefficient from A14A1 table
    - Returns standard outputs: Velocity, Velocity Pressure, Loss Coefficient, and Pressure Loss
    """

    # Extract inputs
    H = stored_values.get("entry_1")
    W = stored_values.get("entry_2")
    Q = stored_values.get("entry_3")
    n = stored_values.get("entry_4")

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, W = {W}, Q = {Q}, n = {n}")

    if None in (H, W, Q, n):
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

        print(f"[DEBUG] Computed: Area = {A:.2f} in^2, Velocity = {V:.2f} ft/min")

        # Look up loss coefficient from A14A1 data
        df = data.loc["A14A1"]
        df = df[["n, free area ratio", "C"]].dropna()
        n_vals = df["n, free area ratio"].unique()
        n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
        C = df[df["n, free area ratio"] == n_match]["C"].values[0]

        print(f"[DEBUG] Matched n = {n_match}, Coefficient C = {C}")

        vp = (V / 4005) ** 2
        pressure_loss = C * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A14A2_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }


A14A2_outputs.output_type = "standard"