import math
import pandas as pd
from data_access import get_case_table


def A13E2_outputs(stored_values, *_):
    """
    A13E2 - Rectangular exit with optional screen.

    Inputs (stored_values):
        entry_1: H  (height, in)
        entry_2: W  (width, in)
        entry_3: L  (length, in)
        entry_4: R  (radius, in)
        entry_5: Q  (flow rate, cfm)
        entry_6: obstruction  ('none', 'none (open)', 'screen', ...)
        entry_7: n  (free area ratio, for screen only)

    Returns (dict):
        Output 1: Velocity (ft/min)
        Output 2: Velocity Pressure (in w.c.)
        Output 3: Loss Coefficient
        Output 4: Pressure Loss (in w.c.)
    """
    # Extract inputs
    H = stored_values.get("entry_1")   # in
    W = stored_values.get("entry_2")   # in
    L = stored_values.get("entry_3")   # in
    R = stored_values.get("entry_4")   # in
    Q = stored_values.get("entry_5")   # cfm
    obstruction = stored_values.get("entry_6")
    n = stored_values.get("entry_7")   # free area ratio if screen

    try:
        # Validate required fields
        if None in (H, W, L, R, Q):
            return {
                "Output 1: Velocity (ft/min)": None,
                "Output 2: Velocity Pressure (in w.c.)": None,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss (in w.c.)": None,
            }

        # --- Geometry & velocity ---
        A = H * W                     # in²
        V = Q / (A / 144.0)           # ft/min
        vp = (V / 4005.0) ** 2        # in w.c.

        R_W = R / W
        L_W = L / W

        # --- Base loss coefficient from A13E2 ---
        df_A13E2 = get_case_table("A13E2")
        df = df_A13E2[["R/W", "L/W", "C"]].dropna()

        RW_vals = df["R/W"].unique()
        LW_vals = df["L/W"].unique()

        # Floor R/W and L/W to the nearest tabulated values
        RW_match = max([val for val in RW_vals if val <= R_W], default=min(RW_vals))
        LW_match = max([val for val in LW_vals if val <= L_W], default=min(LW_vals))

        matched_row = df[(df["R/W"] == RW_match) & (df["L/W"] == LW_match)]
        if matched_row.empty:
            return {"Error": "No matching R/W and L/W pair found in A13E2 data."}

        C_base = matched_row["C"].values[0]

        # --- Optional screen correction from A14A1 ---
        total_C = C_base
        if (
            obstruction is not None
            and isinstance(obstruction, str)
            and "screen" in obstruction.strip().lower()
            and n is not None
        ):
            df_screen = get_case_table("A14A1")
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()

            n_match = max(
                [val for val in n_vals if val <= n],
                default=min(n_vals),
            )
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            total_C = C_base + C1   # matches your original logic

        pressure_loss = total_C * vp

        return {
            "Output 1: Velocity (ft/min)": V,
            "Output 2: Velocity Pressure (in w.c.)": vp,
            "Output 3: Loss Coefficient": total_C,
            "Output 4: Pressure Loss (in w.c.)": pressure_loss,
        }

    except Exception as e:
        return {
            "Output 1: Velocity (ft/min)": None,
            "Output 2: Velocity Pressure (in w.c.)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss (in w.c.)": None,
            "Error": str(e),
        }


A13E2_outputs.output_type = "standard"
