import math
import pandas as pd
from data_access import get_case_table


def A12G_outputs(stored_values, *_):
    """
    Calculates outputs for case A12G:
    - Handles both round and rectangular hood profiles
    - Supports optional screen correction

    Inputs (stored_values):
        entry_1: profile
            "round hood" or "square or rectangular hood"
        If profile == "round hood":
            entry_2: D1  (hood inlet diameter, in)
            entry_3: D   (duct diameter, in)
            entry_4: angle (deg)
            entry_5: Q   (cfm)
            entry_6: obstruction ("none" or "screen")
            entry_7: n   (free area ratio, for screen)
        If profile == "square or rectangular hood":
            entry_2: H1  (hood height, in)
            entry_3: W1  (hood width, in)
            entry_4: D   (duct diameter, in)
            entry_5: angle (deg)
            entry_6: Q   (cfm)
            entry_7: obstruction ("none" or "screen")
            entry_8: n   (free area ratio, for screen)

    Returns:
        dict with:
            Output 1: Velocity
            Output 2: Velocity Pressure
            Output 3: Loss Coefficient
            Output 4: Pressure Loss
    """
    profile = stored_values.get("entry_1")

    try:
        # -----------------------------
        #  Extract profile-specific inputs
        # -----------------------------
        if profile == "round hood":
            D1 = stored_values.get("entry_2")
            D  = stored_values.get("entry_3")
            angle = stored_values.get("entry_4")
            Q  = stored_values.get("entry_5")
            obstruction = stored_values.get("entry_6")
            n  = stored_values.get("entry_7")

            if None in (D1, D, angle, Q):
                return {
                    "Output 1: Velocity": None,
                    "Output 2: Velocity Pressure": None,
                    "Output 3: Loss Coefficient": None,
                    "Output 4: Pressure Loss": None,
                }

            # Downstream (duct) area in²
            A = math.pi * (D / 2.0) ** 2
            # Hood opening area in²
            A1 = math.pi * (D1 / 2.0) ** 2

        elif profile == "square or rectangular hood":
            H1 = stored_values.get("entry_2")
            W1 = stored_values.get("entry_3")
            D  = stored_values.get("entry_4")
            angle = stored_values.get("entry_5")
            Q  = stored_values.get("entry_6")
            obstruction = stored_values.get("entry_7")
            n  = stored_values.get("entry_8")

            if None in (H1, W1, D, angle, Q):
                return {
                    "Output 1: Velocity": None,
                    "Output 2: Velocity Pressure": None,
                    "Output 3: Loss Coefficient": None,
                    "Output 4: Pressure Loss": None,
                }

            # Downstream (duct) area in²
            A = math.pi * (D / 2.0) ** 2
            # Hood opening area in²
            A1 = H1 * W1

        else:
            return {"Error": "Invalid profile. Expected 'round hood' or 'square or rectangular hood'."}

        # -----------------------------
        #  Velocity in the duct
        # -----------------------------
        V = Q / (A / 144.0)  # ft/min

        # -----------------------------
        #  Base loss coefficient (A12G)
        # -----------------------------
        df = get_case_table("A12G")

        config_key = "round hood" if profile == "round hood" else "rect hood"
        df = df[
            (df["configuration"].str.lower() == config_key.lower()) &
            (df["ANGLE"] == angle)
        ]

        if df.empty:
            return {"Error": "No matching data found for A12G configuration and angle."}

        C = df.iloc[0]["C"]

        # -----------------------------
        #  Screen correction (A14A1)
        # -----------------------------
        if obstruction == "screen" and n is not None:
            df_screen = get_case_table("A14A1")
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()

            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max(
                [val for val in n_vals if val <= n],
                default=min(n_vals),
            )
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            # (A1 / A)^2 term
            if A > 0:
                area_ratio_sq = (A1 / A) ** 2
            else:
                area_ratio_sq = 1.0

            C = C + (C1 / area_ratio_sq)

        # -----------------------------
        #  Final outputs
        # -----------------------------
        vp = (V / 4005.0) ** 2
        pressure_loss = C * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
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


A12G_outputs.output_type = "standard"
