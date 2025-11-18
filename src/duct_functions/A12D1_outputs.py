import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A12D1_outputs(stored_values, *_):
    """
    Calculates outputs for case A12D1:
    - Uses L, D, Ds to calculate angle and L/D
    - Looks up loss coefficient C based on L/D (rounded down) and angle (nearest)
    - If obstruction is 'screen', applies correction from A14A1 using free area ratio 'n'
    - Final loss coefficient: C or C + C1/(A_s/A)^2

    Inputs (stored_values):
        entry_1: L   (length, in)
        entry_2: D   (duct diameter, in)
        entry_3: Ds  (exit diameter, in)
        entry_4: Q   (flow rate, cfm)
        entry_5: obstruction ("none" or "screen")
        entry_6: n   (free area ratio, for screen)
    """

    # Extract inputs
    L = stored_values.get("entry_1")   # Length (in)
    D = stored_values.get("entry_2")   # Duct diameter (in)
    Ds = stored_values.get("entry_3")  # Exit diameter (in)
    Q = stored_values.get("entry_4")   # Flow rate (cfm)
    obstruction = stored_values.get("entry_5")  # Obstruction type
    n = stored_values.get("entry_6")   # Free area ratio if obstruction = screen

    # Validate required fields
    if None in (L, D, Ds, Q):
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
        A = math.pi * (D / 2.0) ** 2      # in²
        V = Q / (A / 144.0)               # ft/min

        # L/D and included angle based on D → Ds over length L
        L_D = L / D
        angle_rad = 2.0 * math.atan((Ds - D) / (2.0 * L))
        angle_deg = math.degrees(angle_rad)
        angle_rounded = int(round(angle_deg))

        # ==========================
        #   BASE COEFFICIENT C (A12D1)
        # ==========================
        df = get_case_table("A12D1")
        df = df[["L/D", "ANGLE", "C"]].dropna()

        L_D_vals = df["L/D"].unique()
        angle_vals = df["ANGLE"].unique()

        # L/D: round down to nearest table value (or min if below range)
        L_D_match = max(
            [val for val in L_D_vals if val <= L_D],
            default=min(L_D_vals),
        )
        # ANGLE: nearest table angle
        angle_match = min(angle_vals, key=lambda x: abs(x - angle_rounded))

        row = df[(df["L/D"] == L_D_match) & (df["ANGLE"] == angle_match)]
        if row.empty:
            return {"Error": "No matching L/D and angle found in A12D1 data."}

        C = row["C"].values[0]

        # ==========================
        #   SCREEN CORRECTION (A14A1)
        # ==========================
        if obstruction == "screen" and n is not None:
            df_screen = get_case_table("A14A1")
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()

            # Largest table n <= actual, or smallest if below range
            n_match = max(
                [val for val in n_vals if val <= n],
                default=min(n_vals),
            )
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            A_s = A * n
            correction_factor = C1 / (A_s / A) ** 2
            loss_coefficient = C + correction_factor
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


A12D1_outputs.output_type = "standard"
