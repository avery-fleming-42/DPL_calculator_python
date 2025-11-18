import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A12D2_outputs(stored_values, *_):
    """
    Calculates outputs for case A12D2 (rectangular duct entry):
    - Uses L, H, W, Hs, Ws to compute entry/exit equivalent diameters and angle
    - Uses equivalent diameter to calculate L/D and velocity
    - If obstruction is 'screen', applies correction using free area ratio n

    Inputs (stored_values):
        entry_1: L   (length, in)
        entry_2: H   (entry height, in)
        entry_3: W   (entry width, in)
        entry_4: Hs  (exit height, in)
        entry_5: Ws  (exit width, in)
        entry_6: Q   (flow rate, cfm)
        entry_7: obstruction ("none" or "screen")
        entry_8: n   (free area ratio, for screen)
    """

    # Extract inputs
    L  = stored_values.get("entry_1")
    H  = stored_values.get("entry_2")
    W  = stored_values.get("entry_3")
    Hs = stored_values.get("entry_4")
    Ws = stored_values.get("entry_5")
    Q  = stored_values.get("entry_6")
    obstruction = stored_values.get("entry_7")
    n  = stored_values.get("entry_8")

    # Validate required fields
    if None in (L, H, W, Hs, Ws, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # ==========================
        #   GEOMETRY & VELOCITY
        # ==========================
        # Areas (in²)
        A_entry = H * W
        A_exit  = Hs * Ws  # kept for clarity, not directly used in calcs

        # Equivalent diameters (in) using 1 / [2(H+W)/(HW)]
        D_entry = 1.0 / (2.0 * (H  +  W)  / (H  *  W))
        D_exit  = 1.0 / (2.0 * (Hs +  Ws) / (Hs * Ws))

        # Velocity based on entry area
        V = Q / (A_entry / 144.0)  # ft/min

        # L/D based on entry equivalent diameter
        L_D = L / D_entry

        # Included angle based on change in equivalent diameter over length
        angle_rad = 2.0 * math.atan((D_exit - D_entry) / (2.0 * L))
        angle_deg = math.degrees(angle_rad)
        angle_rounded = int(round(angle_deg))

        # ==========================
        #   BASE COEFFICIENT C (A12D2)
        # ==========================
        df = get_case_table("A12D2")
        df = df[["L/D", "ANGLE", "C"]].dropna()

        L_D_vals    = df["L/D"].unique()
        angle_vals  = df["ANGLE"].unique()

        # L/D: round down to nearest table value (or min if below)
        L_D_match = max(
            [val for val in L_D_vals if val <= L_D],
            default=min(L_D_vals),
        )
        # ANGLE: nearest table angle
        angle_match = min(angle_vals, key=lambda x: abs(x - angle_rounded))

        matched = df[(df["L/D"] == L_D_match) & (df["ANGLE"] == angle_match)]
        if matched.empty:
            return {"Error": "No matching L/D and ANGLE pair in A12D2 data."}

        C = matched["C"].values[0]

        # ==========================
        #   SCREEN CORRECTION (A14A1)
        # ==========================
        if obstruction == "screen" and n is not None:
            df_screen = get_case_table("A14A1")
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()

            # Largest table n <= actual, or smallest if below
            n_match = max(
                [val for val in n_vals if val <= n],
                default=min(n_vals),
            )
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            # Note: As/A_entry = n ⇒ As = n * A_entry
            A_s = A_entry * n
            correction = C1 / (A_s / A_entry) ** 2
            loss_coefficient = C + correction
        else:
            loss_coefficient = C

        # ==========================
        #   OUTPUTS
        # ==========================
        vp = (V / 4005.0) ** 2
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }


A12D2_outputs.output_type = "standard"
