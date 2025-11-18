import pandas as pd
import math
from data_access import get_case_table


def A14A1_outputs(stored_values, data):
    """
    Outputs loss coefficient for a screen using free area ratio (n).
    Inputs: D (diameter), Q (cfm), n (free area ratio)
    """
    D = stored_values.get("entry_1")
    Q = stored_values.get("entry_2")
    n = stored_values.get("entry_3")

    print("[DEBUG] Inputs:")
    print(f"  D = {D}, Q = {Q}, n = {n}")

    if None in (D, Q, n):
        print("[DEBUG] Missing one or more required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # Calculate velocity and velocity pressure
        A = math.pi * (D / 2) ** 2  # in²
        V = Q / (A / 144)  # ft/min
        vp = (V / 4005) ** 2

        # Find base coefficient from A14A1 data (use get_case_table)
        df = get_case_table("A14A1")
        df = df[["n, free area ratio", "C"]].dropna()

        n_vals = df["n, free area ratio"].unique()
        n_match = max([val for val in n_vals if val <= n], default=min(n_vals))

        matched_row = df[df["n, free area ratio"] == n_match]
        if matched_row.empty:
            print("[DEBUG] No matching n found in A14A1.")
            return {
                "Output 1: Velocity": V,
                "Output 2: Velocity Pressure": vp,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss": None,
                "Error": "No matching n found."
            }

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss": C * vp,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A14A1_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }


A14A1_outputs.output_type = "standard"
