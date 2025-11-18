import math
import pandas as pd
from data_access import get_case_table


def A13F1_outputs(stored_values, *_):
    """
    A13F1 - Side/tail exit with V/V0-based loss coefficient.

    Inputs (stored_values):
        entry_1: H      (height, in)
        entry_2: W      (width, in)
        entry_3: angle  (deg)
        entry_4: v_ref  (reference velocity, ft/s)
        entry_5: Q      (flow, cfm)
        entry_6: obstruction  ('none', 'screen', etc.)
        entry_7: n      (free area ratio, for screen)

    Returns:
        Output 1: Velocity (ft/min)
        Output 2: Velocity Ratio (V/V0)
        Output 3: Loss Coefficient
        Output 4: Pressure Loss (in w.c.)
    """
    H      = stored_values.get("entry_1")
    W      = stored_values.get("entry_2")
    angle  = stored_values.get("entry_3")
    v_ref  = stored_values.get("entry_4")  # fps
    Q      = stored_values.get("entry_5")  # cfm
    obstruction = stored_values.get("entry_6")
    n      = stored_values.get("entry_7")  # free area ratio if screen

    try:
        # Required inputs check
        if None in (H, W, angle, v_ref, Q):
            return {
                "Output 1: Velocity (ft/min)": None,
                "Output 2: Velocity Ratio (V/V0)": None,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss (in w.c.)": None,
            }

        # --- Geometry & velocities ---
        A = H * W                 # in²
        V = Q / (A / 144.0)       # ft/min
        V_fps = V / 60.0          # ft/s
        V_V0 = V_fps / v_ref

        aspect_ratio = H / W

        # --- Lookup base C from A13F1 ---
        df_all = get_case_table("A13F1")
        df = df_all[["H/W", "ANGLE", "V/V0", "C"]].dropna()

        # Bucket on H/W category (table uses strings like '0.1-0.2', '0.5-2.0', '5-10')
        if aspect_ratio <= 0.2:
            df_filtered = df[df["H/W"] == "0.1-0.2"]
        elif aspect_ratio <= 2.0:
            df_filtered = df[df["H/W"] == "0.5-2.0"]
        else:
            df_filtered = df[df["H/W"] == "5-10"]

        # Fallback: if that bucket is empty for some reason, just use all rows
        if df_filtered.empty:
            df_filtered = df

        angle_vals = df_filtered["ANGLE"].unique()
        vv_vals    = df_filtered["V/V0"].unique()

        # Angle: floor to nearest tabulated ≤ angle
        angle_match = max([val for val in angle_vals if val <= angle], default=min(angle_vals))
        # V/V0: ceiling to nearest tabulated ≥ V_V0
        vv_match = min([val for val in vv_vals if val >= V_V0], default=max(vv_vals))

        match = df_filtered[(df_filtered["ANGLE"] == angle_match) &
                            (df_filtered["V/V0"] == vv_match)]
        if match.empty:
            return {"Error": "No matching row found in A13F1 data."}

        C_base = match["C"].values[0]

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

            # For this case you're treating the screen as same area as opening → C_total = C + C1
            C_total = C_base + C1

        vp = (V / 4005.0) ** 2
        pressure_loss = C_total * vp

        return {
            "Output 1: Velocity (ft/min)": V,
            "Output 2: Velocity Ratio (V/V0)": V_V0,
            "Output 3: Loss Coefficient": C_total,
            "Output 4: Pressure Loss (in w.c.)": pressure_loss,
        }

    except Exception as e:
        return {
            "Output 1: Velocity (ft/min)": None,
            "Output 2: Velocity Ratio (V/V0)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss (in w.c.)": None,
            "Error": str(e),
        }


A13F1_outputs.output_type = "standard"
