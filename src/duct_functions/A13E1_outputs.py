import math
import pandas as pd
from data_access import get_case_table

def A13E1_outputs(stored_values, data):
    """
    Calculates outputs for A13E1 - Circular duct exit with wall opening
    Inputs: D (in), L (in), Q (cfm), obstruction, [n if screen selected]
    """

    D = stored_values.get("entry_1")  # Diameter
    L = stored_values.get("entry_2")  # Length
    Q = stored_values.get("entry_3")  # Flow rate (cfm)
    obstruction = stored_values.get("entry_4")
    n = stored_values.get("entry_5")  # Optional if screen selected

    print("[DEBUG] Inputs:")
    print(f"  D = {D}, L = {L}, Q = {Q}, obstruction = {obstruction}, n = {n}")

    if None in (D, L, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = math.pi * (D / 2) ** 2  # Area in in^2
        V = Q / (A / 144)  # ft/min
        vp = (V / 4005) ** 2

        L_D = L / D
        print(f"[DEBUG] L/D = {L_D:.4f}, Velocity = {V:.2f}")

        df = data.loc["A13E1"]
        df = df[["L/D", "C"]].dropna()

        LD_vals = df["L/D"].unique()
        LD_match = min([val for val in LD_vals if val >= L_D], default=max(LD_vals))
        print(f"[DEBUG] Matched L/D = {LD_match}")

        matched_row = df[df["L/D"] == LD_match]
        if matched_row.empty:
            return {"Error": "No matching L/D value found in A13E1 data."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base loss coefficient C = {C}")

        # Obstruction correction
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C_screen = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen correction C_screen = {C_screen}")
            total_C = C + C_screen
        else:
            total_C = C

        pressure_loss = total_C * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": total_C,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception in A13E1_outputs: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A13E1_outputs.output_type = "standard"