import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A12A2_outputs(stored_values, *_):
    """
    Calculates outputs for case A12A2 (rectangular duct entry), accounting for:
    - duct geometry (t/D and L/D based on equivalent diameter)
    - optional obstruction ("screen" or "perforated plate") with correction factor (C1)

    Inputs (stored_values):
        entry_1: t  (duct thickness, in)
        entry_2: L  (length, in)
        entry_3: H  (height, in)
        entry_4: W  (width, in)
        entry_5: Q  (flow rate, cfm)
        entry_6: obstruction ("none", "screen", "perforated plate")
        entry_7: n  (free area ratio, for screen/plate)
        entry_8: plate_thickness (in, for perforated plate)
        entry_9: hole_diameter   (in, for perforated plate)
    """
    # Extract inputs
    t = stored_values.get("entry_1")
    L = stored_values.get("entry_2")
    H = stored_values.get("entry_3")
    W = stored_values.get("entry_4")
    Q = stored_values.get("entry_5")
    obstruction = stored_values.get("entry_6")
    n = stored_values.get("entry_7")
    plate_thickness = stored_values.get("entry_8")
    hole_diameter = stored_values.get("entry_9")

    if None in (t, L, H, W, Q):
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
        A = H * W  # in²
        # Equivalent diameter for rectangle (in)
        D_equiv = 1.0 / (2.0 * (H + W) / (H * W))
        V = Q / (A / 144.0)  # ft/min

        t_D = t / D_equiv
        L_D = L / D_equiv

        # ==========================
        #   BASE LOSS COEFFICIENT C (A12A2)
        # ==========================
        df = get_case_table("A12A2")
        df = df[["t/D", "L/D", "C"]].dropna()

        tD_vals = df["t/D"].unique()
        LD_vals = df["L/D"].unique()

        # t/D: round down to nearest table value (or min if below range)
        tD_match = max([val for val in tD_vals if val <= t_D], default=min(tD_vals))
        # L/D: round up to nearest table value (or max if above range)
        LD_match = min([val for val in LD_vals if val >= L_D], default=max(LD_vals))

        matched_row = df[(df["t/D"] == tD_match) & (df["L/D"] == LD_match)]
        if matched_row.empty:
            return {"Error": "No matching t/D and L/D pair found in A12A2 data."}

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

            n_match = max(
                [val for val in n_vals if val <= n],
                default=min(n_vals),
            )
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

        elif obstruction == "perforated plate" and None not in (n, plate_thickness, hole_diameter):
            # Perforated plate correction from A14B1
            try:
                df_plate = get_case_table("A14B1")
            except KeyError:
                return {"Error": "A14B1 data (perforated plate correction) not found."}

            df_plate = df_plate[["n, free area ratio", "t/D", "C"]].dropna()

            plate_t_D = plate_thickness / hole_diameter

            match = df_plate[
                (df_plate["n, free area ratio"] <= n)
                & (df_plate["t/D"] <= plate_t_D)
            ]
            if match.empty:
                return {"Error": "No matching perforated plate correction in A14B1."}

            n_match = max(match["n, free area ratio"].unique())
            tD_sub = match[match["n, free area ratio"] == n_match]
            tD_match_plate = max(tD_sub["t/D"].unique())
            C1 = tD_sub[tD_sub["t/D"] == tD_match_plate]["C"].values[0]

        # ==========================
        #   TOTAL LOSS COEFFICIENT
        # ==========================
        if obstruction in ("screen", "perforated plate"):
            if t_D <= 0.05:
                loss_coefficient = 1.0 + C1
            else:
                loss_coefficient = C + C1
        else:
            loss_coefficient = C

        vp = (V / 4005.0) ** 2
        total_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": total_loss,
        }

    except Exception as e:
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }


A12A2_outputs.output_type = "standard"
