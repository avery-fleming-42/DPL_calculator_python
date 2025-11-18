import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A12C_outputs(stored_values, data):
    """
    Calculates the outputs for case A12B, accounting for:
    - bellmouth entry with R/D to determine base coefficient
    - optional screen obstruction with correction factor
    """

    # Extract inputs
    R = stored_values.get("entry_1")  # Bellmouth radius
    D = stored_values.get("entry_2")  # Duct diameter
    Ds = stored_values.get("entry_3")  # Exit diameter
    Q = stored_values.get("entry_4")  # Flow rate
    obstruction = stored_values.get("entry_5")  # "none" or "screen"
    n = stored_values.get("entry_6")  # free area ratio (only for screen)

    print("[DEBUG] Inputs:")
    print(f"  R = {R}, D = {D}, Ds = {Ds}, Q = {Q}")
    print(f"  obstruction = {obstruction}, n = {n}")

    # Return blank output if required inputs are missing
    if None in (R, D, Ds, Q):
        print("[DEBUG] Missing one or more required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # Calculate velocity based on exit diameter
        A = math.pi * (Ds / 2) ** 2  # in²
        V = Q / (A / 144)  # ft/min

        R_D = R / D
        print(f"[DEBUG] Computed: R/D = {R_D:.4f}, Velocity = {V:.2f}")

        # Base coefficient from A12B data
        df = data.loc["A12C"]
        df = df[["R/D", "C"]].dropna()

        r_d_vals = df["R/D"].unique()
        r_d_match = max([val for val in r_d_vals if val <= R_D], default=min(r_d_vals))

        matched_row = df[df["R/D"] == r_d_match]
        if matched_row.empty:
            print("[DEBUG] No match found in A12B table.")
            return {"Error": "No matching R/D found in data."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        # Obstruction correction (screen only)
        C1 = 0
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen obstruction C1 = {C1}")

        if obstruction == "screen":
            A_s = n * A
            loss_coefficient = C + (C1 / (A_s / A) ** 2)
            print("[DEBUG] Obstruction present: C + C1 / (As/A)^2")
        else:
            loss_coefficient = C
            print("[DEBUG] No obstruction: using base C only")

        print(f"[DEBUG] Final Loss Coefficient = {loss_coefficient}")

        # Final outputs
        vp = (V / 4005) ** 2
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A12B_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A12C_outputs.output_type = "standard"