import math
import pandas as pd
from data_access import get_case_table


def A13F2_outputs(stored_values, *_):
    """
    A13F2 - Round duct exit with varying angle and obstruction type.

    Inputs (stored_values):
        entry_1: D      (duct diameter, in)
        entry_2: angle  (deg)
        entry_3: v_ref  (reference velocity, ft/min)
        entry_4: Q      (flow, cfm)
        entry_5: obstruction  ("none", "screen", etc.)
        entry_6: n      (free area ratio, for screen)

    Returns:
        Output 1: Velocity (ft/min)
        Output 2: Velocity Pressure (in w.c.)
        Output 3: Loss Coefficient
        Output 4: Pressure Loss (in w.c.)
    """
    D          = stored_values.get("entry_1")
    angle      = stored_values.get("entry_2")
    v_ref      = stored_values.get("entry_3")  # ft/min
    Q          = stored_values.get("entry_4")  # cfm
    obstruction = stored_values.get("entry_5")
    n          = stored_values.get("entry_6")

    try:
        # Required inputs check
        if None in (D, angle, v_ref, Q):
            return {
                "Output 1: Velocity (ft/min)": None,
                "Output 2: Velocity Pressure (in w.c.)": None,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss (in w.c.)": None,
            }

        # --- Geometry & velocities ---
        A = math.pi * (D / 2.0) ** 2     # in²
        V = Q / (A / 144.0)              # ft/min
        vv_ratio = V / v_ref             # dimensionless V/V0

        # --- Lookup base C from A13F2 ---
        df_all = get_case_table("A13F2")
        df = df_all[["ANGLE", "V/V0", "C"]].dropna()

        angle_vals = df["ANGLE"].unique()
        vv_vals    = df["V/V0"].unique()

        # Angle: floor to nearest tabulated ≤ angle
        angle_match = max([val for val in angle_vals if val <= angle], default=min(angle_vals))
        # V/V0: ceiling to nearest tabulated ≥ V/V0
        vv_match = min([val for val in vv_vals if val >= vv_ratio], default=max(vv_vals))

        matched_row = df[(df["ANGLE"] == angle_match) &
                         (df["V/V0"] == vv_match)]
        if matched_row.empty:
            return {"Error": "No matching data found for given angle and V/V0 in A13F2."}

        C_base = matched_row["C"].values[0]

        # --- Screen obstruction correction (A14A1) ---
        C_total = C_base
        if (
            obstruction is not None
            and isinstance(obstruction, str)
            and "screen" in obstruction.strip().lower()
            and n is not None
        ):
            df_screen = get_case_table("A14A1")
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            # For this case you're using a simple additive correction: C_total = C + C1
            C_total = C_base + C1

        vp = (V / 4005.0) ** 2
        total_loss = C_total * vp

        return {
            "Output 1: Velocity (ft/min)": V,
            "Output 2: Velocity Pressure (in w.c.)": vp,
            "Output 3: Loss Coefficient": C_total,
            "Output 4: Pressure Loss (in w.c.)": total_loss,
        }

    except Exception as e:
        return {
            "Output 1: Velocity (ft/min)": None,
            "Output 2: Velocity Pressure (in w.c.)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss (in w.c.)": None,
            "Error": str(e),
        }


A13F2_outputs.output_type = "standard"
