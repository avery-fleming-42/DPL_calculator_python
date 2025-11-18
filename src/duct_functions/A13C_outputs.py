import math
import pandas as pd
from data_access import get_case_table


def A13C_outputs(stored_values, *_):
    """
    A13C: Rectangular Conical Exit with or without Wall

    Inputs (stored_values):
        entry_1: H    (height, in)
        entry_2: Hs   (exit height, in)
        entry_3: W    (width, in)
        entry_4: angle (deg)
        entry_5: Q    (cfm)
        entry_6: obstruction ("none", "screen", etc.)
        entry_7: n    (free area ratio, if screen)

    Returns:
        dict with Velocity, Velocity Pressure, Loss Coefficient, Pressure Loss
        or None values on missing inputs / error.
    """
    H = stored_values.get("entry_1")   # height (in)
    Hs = stored_values.get("entry_2")  # exit height (in)
    W = stored_values.get("entry_3")   # width (in)
    angle = stored_values.get("entry_4")  # degrees
    Q = stored_values.get("entry_5")   # flow rate (cfm)
    obstruction = stored_values.get("entry_6")  # "none" or "screen"
    n = stored_values.get("entry_7")   # free area ratio if screen

    if None in (H, Hs, W, angle, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # Areas (in²) and ratio
        A = H * W
        As = Hs * W
        A_ratio = As / A if A != 0 else 1.0

        # Velocity & VP
        V = Q / (A / 144.0)  # ft/min
        vp = (V / 4005.0) ** 2

        # ---------- Base C from A13C ----------
        df = get_case_table("A13C")
        df = df[["ANGLE", "As/A", "C"]].dropna()

        # Angle: round "up" (smallest tabulated ≥ input, else max)
        angle_vals = df["ANGLE"].unique()
        angle_match = min(
            [val for val in angle_vals if val >= angle],
            default=max(angle_vals),
        )

        # Area ratio selection depends on angle
        ratio_subset = df[df["ANGLE"] == angle_match]["As/A"].unique()
        if angle <= 20:
            # For small angles: largest tabulated ≤ A_ratio
            ratio_match = max(
                [val for val in ratio_subset if val <= A_ratio],
                default=min(ratio_subset),
            )
        else:
            # For larger angles: closest ratio
            ratio_match = min(ratio_subset, key=lambda x: abs(x - A_ratio))

        matched_row = df[(df["ANGLE"] == angle_match) & (df["As/A"] == ratio_match)]
        if matched_row.empty:
            return {"Error": "No matching data in A13C for given angle and area ratio."}

        C_base = matched_row["C"].values[0]

        # ---------- Screen correction (A14A1) ----------
        loss_coefficient = C_base
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

            # C_total = C + C1 / (As/A)²
            loss_coefficient = C_base + (C1 / (A_ratio ** 2 if A_ratio != 0 else 1.0))

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


A13C_outputs.output_type = "standard"
