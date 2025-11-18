import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A12D2_outputs(stored_values, data):
    """
    Calculates outputs for case A12D2 (rectangular duct entry):
    - Uses L, H, W, Hs, Ws to compute entry/exit equivalent diameters and angle
    - Uses equivalent diameter to calculate L/D and velocity
    - If obstruction is 'screen', applies correction using n
    """

    # Extract inputs
    L = stored_values.get("entry_1")    # Length (in)
    H = stored_values.get("entry_2")    # Entry height
    W = stored_values.get("entry_3")    # Entry width
    Hs = stored_values.get("entry_4")   # Exit height
    Ws = stored_values.get("entry_5")   # Exit width
    Q = stored_values.get("entry_6")    # Flow rate
    obstruction = stored_values.get("entry_7")  # Obstruction type
    n = stored_values.get("entry_8")    # Free area ratio (if applicable)

    print("[DEBUG] Inputs:")
    print(f"  L = {L}, H = {H}, W = {W}, Hs = {Hs}, Ws = {Ws}, Q = {Q}")
    print(f"  obstruction = {obstruction}, n = {n}")

    if None in (L, H, W, Hs, Ws, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # Entry/Exit cross-sectional areas (in²)
        A_entry = H * W
        A_exit = Hs * Ws

        # Equivalent diameters (in)
        D_entry = 2 * (H + W) / (H * W)
        D_exit = 2 * (Hs + Ws) / (Hs * Ws)

        D_entry = 1 / D_entry
        D_exit = 1 / D_exit

        # Use entry area and D_entry for calculations
        V = Q / (A_entry / 144)  # ft/min
        t_D = L / D_entry

        # Calculate angle from D_exit and D_entry
        angle_rad = 2 * math.atan((D_exit - D_entry) / (2 * L))
        angle_deg = math.degrees(angle_rad)
        angle_rounded = int(round(angle_deg))

        print(f"[DEBUG] Computed: D_entry = {D_entry:.2f}, D_exit = {D_exit:.2f}, L/D = {t_D:.4f}, angle = {angle_deg:.2f}°")

        # Pull from A12D2
        df = data.loc["A12D2"]
        df = df[["L/D", "ANGLE", "C"]].dropna()

        L_D_vals = df["L/D"].unique()
        angle_vals = df["ANGLE"].unique()

        L_D_match = max([val for val in L_D_vals if val <= t_D], default=min(L_D_vals))
        angle_match = min(angle_vals, key=lambda x: abs(x - angle_rounded))

        matched = df[(df["L/D"] == L_D_match) & (df["ANGLE"] == angle_match)]
        if matched.empty:
            return {"Error": "No matching L/D and ANGLE pair in A12D2"}

        C = matched["C"].values[0]
        print(f"[DEBUG] Base loss coefficient C = {C}")

        # Apply screen obstruction correction
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            A_s = A_entry * n
            correction = C1 / (A_s / A_entry) ** 2
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
        print(f"[ERROR] Exception in A12D2_outputs: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A12D2_outputs.output_type = "standard"