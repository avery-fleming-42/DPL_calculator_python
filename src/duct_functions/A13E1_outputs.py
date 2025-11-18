import math
import pandas as pd
from data_access import get_case_table


def A13E1_outputs(stored_values, *_):
    """
    A13E1 - Circular duct exit with wall opening.

    Inputs (stored_values):
        entry_1: D  (duct diameter, in)
        entry_2: L  (length, in)
        entry_3: Q  (flow rate, cfm)
        entry_4: obstruction  ('none', 'screen', etc.)
        entry_5: n  (free area ratio, for screen)

    Returns (dict):
        Output 1: Velocity (ft/min)
        Output 2: Velocity Pressure (in w.c.)
        Output 3: Loss Coefficient
        Output 4: Pressure Loss (in w.c.)
    """
    # Extract inputs
    D = stored_values.get("entry_1")   # Diameter (in)
    L = stored_values.get("entry_2")   # Length (in)
    Q = stored_values.get("entry_3")   # Flow rate (cfm)
    obstruction = stored_values.get("entry_4")
    n = stored_values.get("entry_5")   # Free area ratio (if screen)

    try:
        if None in (D, L, Q):
            return {
                "Output 1: Velocity": None,
                "Output 2: Velocity Pressure": None,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss": None,
            }

        # --- Geometry & velocity ---
        A = math.pi * (D / 2.0) ** 2          # in²
        V = Q / (A / 144.0)                   # ft/min
        vp = (V / 4005.0) ** 2               # in w.c.
        L_D = L / D

        # --- Base loss coefficient from A13E1 ---
        df_A13E1 = get_case_table("A13E1")
        df = df_A13E1[["L/D", "C"]].dropna()

        LD_vals = df["L/D"].unique()
        # Round L/D up to the nearest tabulated value (or use max if above range)
        LD_match = min(
            [val for val in LD_vals if val >= L_D],
            default=max(LD_vals),
        )

        matched_row = df[df["L/D"] == LD_match]
        if matched_row.empty:
            return {"Error": "No matching L/D value found in A13E1 data."}

        C_base = matched_row["C"].values[0]

        # --- Optional screen correction from A14A1 ---
        total_C = C_base
        if (
            obstruction is not None
            and isinstance(obstruction, str)
            and obstruction.strip().lower() == "screen"
            and n is not None
        ):
            df_screen = get_case_table("A14A1")
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()

            n_match = max(
                [val for val in n_vals if val <= n],
                default=min(n_vals),
            )
            C_screen = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            total_C = C_base + C_screen

        pressure_loss = total_C * vp

        return {
            "Output 1: Velocity (ft/min)": V,
            "Output 2: Velocity Pressure (in w.c.)": vp,
            "Output 3: Loss Coefficient": total_C,
            "Output 4: Pressure Loss (in w.c.)": pressure_loss,
        }

    except Exception as e:
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }


A13E1_outputs.output_type = "standard"
