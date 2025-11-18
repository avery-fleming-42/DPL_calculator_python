import math
import pandas as pd
from data_access import get_case_table


def A13D_outputs(stored_values, *_):
    """
    Calculates outputs for case A13D (rectangular exit transition with potentially
    different vertical and lateral angles).

    Inputs (stored_values):
        entry_1: H    (initial height, in)
        entry_2: W    (initial width, in)
        entry_3: H_1  (final height, in)
        entry_4: W_1  (final width, in)
        entry_5: L    (transition length, in)
        entry_6: Q    (flow rate, cfm)
        entry_7: obstruction  ('none (open)', 'screen', etc.)
        entry_8: n    (free area ratio, if screen)
    """
    try:
        H = stored_values.get("entry_1")
        W = stored_values.get("entry_2")
        H_1 = stored_values.get("entry_3")
        W_1 = stored_values.get("entry_4")
        L = stored_values.get("entry_5")
        Q = stored_values.get("entry_6")
        obstruction = stored_values.get("entry_7")
        n = stored_values.get("entry_8")

        if None in (H, W, H_1, W_1, L, Q):
            return {
                "Output 1: Velocity": None,
                "Output 2: Velocity Pressure": None,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss": None,
            }

        # Areas and ratios
        A = H * W              # in²
        A_s = H_1 * W_1        # in²
        if A == 0:
            return {"Error": "Invalid geometry: main area is zero."}

        area_ratio = A_s / A

        # Velocity at smaller section (upstream)
        V = Q / (A / 144.0)  # ft/min
        vp = (V / 4005.0) ** 2

        # Compute lateral and vertical angles (deg)
        lateral_angle = math.degrees(2 * math.atan((W_1 - W) / (2 * L)))
        vertical_angle = math.degrees(2 * math.atan((H_1 - H) / (2 * L)))
        angle = max(lateral_angle, vertical_angle)

        # ---------- Lookup base C from A13D ----------
        df_A13D = get_case_table("A13D")
        angle_col = "ANGLE"
        ar_col = "As/A"

        angle_vals = df_A13D[angle_col].dropna().unique()
        ar_vals = df_A13D[ar_col].dropna().unique()

        # Angle rounding rule:
        #   ≤ 30° → round down to largest tabulated ≤ angle
        #   > 30° → round up to smallest tabulated ≥ angle
        if angle <= 30:
            angle_match = max(
                [a for a in angle_vals if a <= angle],
                default=min(angle_vals),
            )
        else:
            angle_match = min(
                [a for a in angle_vals if a >= angle],
                default=max(angle_vals),
            )

        # Area ratio rounding: round down to largest tabulated ≤ area_ratio
        ar_match = max(
            [v for v in ar_vals if v <= area_ratio],
            default=min(ar_vals),
        )

        df_match = df_A13D[
            (df_A13D[angle_col] == angle_match) &
            (df_A13D[ar_col] == ar_match)
        ]

        if df_match.empty:
            return {"Error": "No matching loss coefficient found in A13D."}

        C_base = df_match["C"].values[0]

        # ---------- Screen obstruction correction (A14A1) ----------
        total_loss_coefficient = C_base

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
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            As_A = A_s / A if A != 0 else 1.0
            total_loss_coefficient = C_base + (C1 / (As_A ** 2))

        pressure_loss = total_loss_coefficient * vp

        return {
            "Output 1: Velocity (ft/min)": V,
            "Output 2: Velocity Pressure (in w.c.)": vp,
            "Output 3: Loss Coefficient": total_loss_coefficient,
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


A13D_outputs.output_type = "standard"
