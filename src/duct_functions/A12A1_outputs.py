import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A12A1_outputs(stored_values, *_):
    """
    Calculates the outputs for case A12A1, accounting for:
    - duct geometry (t/D and L/D) for base loss coefficient (C)
    - optional obstruction ("screen" or "perforated plate") with correction factor (C1)

    Inputs (stored_values):
        entry_1: t  (duct thickness, in)
        entry_2: L  (length, in)
        entry_3: D  (diameter, in)
        entry_4: Q  (flow rate, cfm)
        entry_5: obstruction ("none", "screen", "perforated plate")
        entry_6: n  (free area ratio, for screen/plate)
        entry_7: plate_thickness (in, for perforated plate)
        entry_8: hole_diameter   (in, for perforated plate)
    """
    # Extract inputs
    t = stored_values.get("entry_1")  # duct thickness
    L = stored_values.get("entry_2")  # length
    D = stored_values.get("entry_3")  # diameter
    Q = stored_values.get("entry_4")  # flow rate (cfm)
    obstruction = stored_values.get("entry_5")  # "none", "screen", "perforated plate"
    n = stored_values.get("entry_6")  # free area ratio (if applicable)
    plate_thickness = stored_values.get("entry_7")  # for perforated plate
    hole_diameter = stored_values.get("entry_8")  # for perforated plate

    if None in (t, L, D, Q):
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
        # Area in in², then velocity in ft/min
        A = math.pi * (D / 2.0) ** 2  # in²
        V = Q / (A / 144.0)           # ft/min

        t_D = t / D
        L_D = L / D

        # ==========================
        #   BASE LOSS COEFFICIENT C (A12A1)
        # ==========================
        df = get_case_table("A12A1")
        df = df[["t/D", "L/D", "C"]].dropna()

        tD_vals = df["t/D"].unique()
        LD_vals = df["L/D"].unique()

        # t/D: round down to nearest table value (or min if below range)
        tD_match = max([val for val in tD_vals if val <= t_D], default=min(tD_vals))
        # L/D: round up to nearest table value (or max if above range)
        LD_match = min([val for val in LD_vals if val >= L_D], default=max(LD_vals))

        matched_row = df[(df["t/D"] == tD_match) & (df["L/D"] == LD_match)]
        if matched_row.empty:
            return {"Error": "No matching t/D and L/D pair found in A12A1 data."}

        C = matched_row["C"].values[0]

        # ==========================
        #   OBSTRUCTION CORRECTION C1
        # ==========================
        C1 = 0.0

        if obstruction == "screen" and n is not None:
            # Screen correction from A14A1
            try:
                df_screen = get_case_table("A14A1")
            except KeyError:
                return {"Error": "A14A1 data (screen correction) not found."}

            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()

            # Use largest table n <= actual n (or smallest if below range)
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

        elif obstruction == "perforated plate" and None not in (n, plate_thickness, hole_diameter):
            # Perforated plate correction from A14B1
            try:
                df_plate = get_case_table("A14B1")
            except KeyError:
                return {"Error": "A14B1 data (perforated plate correction) not found."}

            df_plate = df_plate[["n, free area ratio", "t/D", "C"]].dropna()

            tD_plate = plate_thickness / hole_diameter

            plate_match = df_plate[
                (df_plate["n, free area ratio"] <= n)
                & (df_plate["t/D"] <= tD_plate)
            ]
            if plate_match.empty:
                return {"Error": "No matching plate correction factor found in A14B1."}

            # Largest n <= actual, then largest t/D within that n
            n_match = max(plate_match["n, free area ratio"].unique())
            tD_sub = plate_match[plate_match["n, free area ratio"] == n_match]
            tD_match_plate = max(tD_sub["t/D"].unique())
            C1 = tD_sub[tD_sub["t/D"] == tD_match_plate]["C"].values[0]

        # ==========================
        #   TOTAL LOSS COEFFICIENT
        # ==========================
        if obstruction in ("screen", "perforated plate"):
            # Thin-plate limit uses 1 + C1, otherwise C + C1
            if t_D <= 0.05:
                loss_coefficient = 1.0 + C1
            else:
                loss_coefficient = C + C1
        else:
            loss_coefficient = C

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


A12A1_outputs.output_type = "standard"
