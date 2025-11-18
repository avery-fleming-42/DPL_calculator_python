import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A12D1_outputs(stored_values, data):
    """
    Calculates outputs for case A12D1:
    - Uses L, D, Ds to calculate angle and L/D
    - Looks up loss coefficient C based on L/D (rounded down) and angle (rounded to nearest)
    - If obstruction is 'screen', applies correction from A14A1 using free area ratio 'n'
    - Final loss coefficient: C or C + C1/(A_s/A)^2
    """

    # Extract inputs
    L = stored_values.get("entry_1")   # Length (in)
    D = stored_values.get("entry_2")   # Duct diameter (in)
    Ds = stored_values.get("entry_3")  # Exit diameter (in)
    Q = stored_values.get("entry_4")   # Flow rate (cfm)
    obstruction = stored_values.get("entry_5")  # Obstruction type
    n = stored_values.get("entry_6")   # Free area ratio if obstruction = screen

    print("[DEBUG] Inputs:")
    print(f"  L = {L}, D = {D}, Ds = {Ds}, Q = {Q}")
    print(f"  obstruction = {obstruction}, n = {n}")

    # Validate required fields
    if None in (L, D, Ds, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None
        }

    try:
        # Compute velocity
        A = math.pi * (D / 2) ** 2
        V = Q / (A / 144)  # ft/min

        # Calculate L/D and angle
        L_D = L / D
        angle_rad = 2 * math.atan((Ds - D) / (2 * L))
        angle_deg = math.degrees(angle_rad)
        angle_rounded = int(round(angle_deg))

        print(f"[DEBUG] Computed: L/D = {L_D:.4f}, angle = {angle_deg:.2f}°, rounded = {angle_rounded}")

        # Base coefficient lookup
        df = data.loc["A12D1"]
        df = df[["L/D", "ANGLE", "C"]].dropna()

        L_D_vals = df["L/D"].unique()
        angle_vals = df["ANGLE"].unique()

        L_D_match = max([val for val in L_D_vals if val <= L_D], default=min(L_D_vals))
        angle_match = min(angle_vals, key=lambda x: abs(x - angle_rounded))

        print(f"[DEBUG] Matched L/D = {L_D_match}, ANGLE = {angle_match}")

        row = df[(df["L/D"] == L_D_match) & (df["ANGLE"] == angle_match)]
        if row.empty:
            return {"Error": "No matching L/D and angle found in data."}
        C = row["C"].values[0]
        print(f"[DEBUG] Base loss coefficient C = {C}")

        # Screen obstruction correction (A14A1)
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            A_s = A * n
            correction_factor = C1 / (A_s / A) ** 2
            loss_coefficient = C + correction_factor

            print(f"[DEBUG] Screen obstruction applied: C1 = {C1}, correction = {correction_factor}")
        else:
            loss_coefficient = C
            print("[DEBUG] No obstruction or not screen; using base C")

        # Final calculations
        vp = (V / 4005) ** 2
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss
        }

    except Exception as e:
        print(f"[ERROR] Exception in A12D1_outputs: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e)
        }

A12D1_outputs.output_type = "standard"