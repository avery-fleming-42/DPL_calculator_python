import math
import pandas as pd
from data_access import get_case_table


def A13B_outputs(stored_values, *_):
    """
    Calculates outputs for case A13B (conical exit with/without wall), accounting for:
    - Base loss coefficient from angle and As/A ratio
    - Optional screen obstruction correction

    Inputs (stored_values):
        entry_1: L   (length, in)
        entry_2: D   (small-end diameter, in)
        entry_3: Ds  (exit diameter, in)
        entry_4: Q   (flow rate, cfm)
        entry_5: obstruction ("none", "screen", etc.)
        entry_6: n   (free area ratio, only for screen)

    Returns:
        dict with:
            Output 1: Velocity
            Output 2: Velocity Pressure
            Output 3: Loss Coefficient
            Output 4: Pressure Loss
            (optional "Error" key on failure)
    """
    # Extract inputs
    L = stored_values.get("entry_1")
    D = stored_values.get("entry_2")
    Ds = stored_values.get("entry_3")
    Q = stored_values.get("entry_4")
    obstruction = stored_values.get("entry_5")
    n = stored_values.get("entry_6")  # Only for screen

    if None in (L, D, Ds, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # Geometry and ratios
        A = math.pi * (D / 2.0) ** 2        # in² (small end)
        As = math.pi * (Ds / 2.0) ** 2      # in² (exit)
        A_ratio = As / A if A > 0 else 1.0  # As/A

        # Cone angle from geometry (deg)
        angle = math.degrees(2.0 * math.atan((Ds - D) / (2.0 * L)))

        # -----------------------------
        #  Base loss coefficient from A13B
        # -----------------------------
        df = get_case_table("A13B")
        df = df[["ANGLE", "As/A", "C"]].dropna()

        angle_vals = sorted(df["ANGLE"].unique())
        ratio_vals = sorted(df["As/A"].unique())

        # Angle: smallest tabulated ≥ computed, else max
        angle_match = min(
            [val for val in angle_vals if val >= angle],
            default=max(angle_vals),
        )

        # As/A: piecewise rule (your original logic)
        if angle < 45:
            # for small angles, pick largest tabulated ≤ actual ratio
            A_ratio_match = max(
                [val for val in ratio_vals if val <= A_ratio],
                default=min(ratio_vals),
            )
        else:
            # for larger angles, pick closest tabulated ratio
            A_ratio_match = min(ratio_vals, key=lambda x: abs(x - A_ratio))

        matched_row = df[(df["ANGLE"] == angle_match) & (df["As/A"] == A_ratio_match)]
        if matched_row.empty:
            return {"Error": "No matching angle and As/A pair found in A13B data."}

        C_base = matched_row["C"].values[0]

        # -----------------------------
        #  Screen correction (A14A1)
        # -----------------------------
        C_total = C_base
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

            # Use As/A ratio from small to large end
            C_total = C_base + (C1 / (A_ratio ** 2 if A_ratio != 0 else 1.0))

        # -----------------------------
        #  Final outputs
        # -----------------------------
        V = Q / (A / 144.0)        # ft/min
        vp = (V / 4005.0) ** 2
        pressure_loss = C_total * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C_total,
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


A13B_outputs.output_type = "standard"
