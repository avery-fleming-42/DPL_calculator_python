import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A12B_outputs(stored_values, *_):
    """
    Calculates the outputs for case A12B, accounting for:
    - bellmouth entry with R/D to determine base coefficient
    - optional screen obstruction with correction factor

    Inputs (stored_values):
        entry_1: R   (bellmouth radius, in)
        entry_2: D   (duct diameter, in)
        entry_3: Ds  (exit diameter, in)
        entry_4: Q   (flow rate, cfm)
        entry_5: obstruction ("none" or "screen")
        entry_6: n   (free area ratio, for screen)
    """

    # Extract inputs
    R = stored_values.get("entry_1")   # Bellmouth radius
    D = stored_values.get("entry_2")   # Duct diameter
    Ds = stored_values.get("entry_3")  # Exit diameter
    Q = stored_values.get("entry_4")   # Flow rate
    obstruction = stored_values.get("entry_5")  # "none" or "screen"
    n = stored_values.get("entry_6")   # Free area ratio (only for screen)

    # Return blank output if required inputs are missing
    if None in (R, D, Ds, Q):
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
        A = math.pi * (Ds / 2.0) ** 2  # in²
        V = Q / (A / 144.0)            # ft/min

        R_D = R / D

        # ==========================
        #   BASE COEFFICIENT C (A12B)
        # ==========================
        df = get_case_table("A12B")
        df = df[["R/D", "C"]].dropna()

        r_d_vals = df["R/D"].unique()
        # Use largest R/D in table that is <= actual, or min if below range
        r_d_match = max(
            [val for val in r_d_vals if val <= R_D],
            default=min(r_d_vals),
        )

        matched_row = df[df["R/D"] == r_d_match]
        if matched_row.empty:
            return {"Error": "No matching R/D found in A12B data."}

        C = matched_row["C"].values[0]

        # ==========================
        #   OBSTRUCTION CORRECTION (SCREEN)
        # ==========================
        C1 = 0.0
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

        # Effective obstruction formula
        if obstruction == "screen":
            A_s = n * A  # free area
            loss_coefficient = C + (C1 / (A_s / A) ** 2)
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


A12B_outputs.output_type = "standard"
