import math
import pandas as pd
from data_access import get_case_table

def A13H_outputs(stored_values, data):
    H = stored_values.get("entry_1")
    W = stored_values.get("entry_2")
    H1 = stored_values.get("entry_3")
    W1 = stored_values.get("entry_4")
    angle = stored_values.get("entry_5")
    Q = stored_values.get("entry_6")
    obstruction = stored_values.get("entry_7")
    n = stored_values.get("entry_8")

    print("[DEBUG] Inputs:")
    print(f"  H={H}, W={W}, H1={H1}, W1={W1}, angle={angle}, Q={Q}, obstruction={obstruction}, n={n}")

    if None in (H, W, H1, W1, angle, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None
        }

    try:
        A = H * W
        A1 = H1 * W1
        V = Q / (A / 144)  # ft/min
        ratio = A1 / A

        # --- Base table for A13H (UPDATED) ---
        df_A13H = get_case_table("A13H")

        angle_vals = df_A13H["ANGLE"].dropna().unique()
        angle_rounded = min(
            [a for a in angle_vals if a >= angle],
            default=max(angle_vals)
        )

        print(f"[DEBUG] Calculated A = {A}, A1 = {A1}, V = {V}, "
              f"Area Ratio = {ratio}, Rounded Angle = {angle_rounded}")

        df = df_A13H[df_A13H["ANGLE"] == angle_rounded]

        ratio_vals = df["A1/A"].dropna().unique()
        ratio_match = max(
            [val for val in ratio_vals if val <= ratio],
            default=min(ratio_vals)
        )

        print(f"[DEBUG] Matched A1/A = {ratio_match}")

        matched_row = df[df["A1/A"] == ratio_match]
        if matched_row.empty:
            return {"Error": "No matching configuration found in A13H table."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base Coefficient C = {C}")

        # --- Obstruction correction via A14A1 (UPDATED) ---
        if obstruction == "screen" and n is not None:
            df_screen = get_case_table("A14A1")
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max(
                [val for val in n_vals if val <= n],
                default=min(n_vals)
            )
            C_screen = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            total_loss_coefficient = C + (C_screen / (A1 / A) ** 2)
            print(f"[DEBUG] Screen C = {C_screen}, "
                  f"Total Loss Coefficient = {total_loss_coefficient}")
        else:
            total_loss_coefficient = C

        vp = (V / 4005) ** 2
        pressure_loss = total_loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": total_loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e)
        }

A13H_outputs.output_type = "standard"
