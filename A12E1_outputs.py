import math
import pandas as pd
import numpy as np

def A12E1_outputs(stored_values, data):
    """
    Calculates outputs for case A12E1 (conical converging bellmouth with end wall, round duct).
    Logic is nearly identical to A12D1, but uses base loss coefficient data from A12E1.
    """

    # Extract inputs
    L = stored_values.get("entry_1")    # Length (in)
    D = stored_values.get("entry_2")    # Entry diameter
    Ds = stored_values.get("entry_3")   # Exit diameter
    Q = stored_values.get("entry_4")    # Flow rate
    obstruction = stored_values.get("entry_5")  # Obstruction type
    n = stored_values.get("entry_6")    # Free area ratio (if applicable)

    print("[DEBUG] Inputs:")
    print(f"  L = {L}, D = {D}, Ds = {Ds}, Q = {Q}")
    print(f"  obstruction = {obstruction}, n = {n}")

    if None in (L, D, Ds, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = math.pi * (D / 2) ** 2  # in²
        V = Q / (A / 144)  # ft/min

        L_D = L / D
        angle_rad = 2 * math.atan((Ds - D) / (2 * L))
        angle_deg = math.degrees(angle_rad)
        angle_rounded = int(round(angle_deg))

        print(f"[DEBUG] Computed: L/D = {L_D:.4f}, angle = {angle_deg:.2f}°")

        # Pull from A12E1
        df = data.loc["A12E1"]
        df = df[["L/D", "ANGLE", "C"]].dropna()

        L_D_vals = df["L/D"].unique()
        angle_vals = df["ANGLE"].unique()

        L_D_match = max([val for val in L_D_vals if val <= L_D], default=min(L_D_vals))
        angle_match = min(angle_vals, key=lambda x: abs(x - angle_rounded))

        matched = df[(df["L/D"] == L_D_match) & (df["ANGLE"] == angle_match)]
        if matched.empty:
            return {"Error": "No matching L/D and ANGLE pair in A12E1"}

        C = matched["C"].values[0]
        print(f"[DEBUG] Base loss coefficient C = {C}")

        # Apply screen obstruction correction if selected
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            A_s = A * n
            correction = C1 / (A_s / A) ** 2
            loss_coefficient = C + correction
            print(f"[DEBUG] Screen obstruction applied: C1 = {C1}, correction = {correction}")
        else:
            loss_coefficient = C
            print("[DEBUG] No obstruction or not screen; using base C")

        vp = (V / 4005) ** 2
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss
        }

    except Exception as e:
        print(f"[ERROR] Exception in A12E1_outputs: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A12E1_outputs.output_type = "standard"