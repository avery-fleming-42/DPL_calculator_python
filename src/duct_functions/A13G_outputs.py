import math
import pandas as pd
from data_access import get_case_table

def A13G_outputs(stored_values, data):
    """
    Calculates outputs for case A13G (rectangular exit with varying height and width), accounting for:
    - area ratio (H1*W / H*W)
    - angle (rounded up)
    - optional obstruction (screen) with correction factor from A14A1
    """

    # Extract inputs
    H = stored_values.get("entry_1")
    W = stored_values.get("entry_2")
    H1 = stored_values.get("entry_3")
    angle = stored_values.get("entry_4")
    Q = stored_values.get("entry_5")
    obstruction = stored_values.get("entry_6")
    n = stored_values.get("entry_7")  # screen free area ratio (optional)

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, W = {W}, H1 = {H1}, angle = {angle}, Q = {Q}, obstruction = {obstruction}, n = {n}")

    if None in (H, W, H1, angle, Q):
        print("[DEBUG] Missing one or more required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = H * W
        V = Q / (A / 144)  # ft/min

        area_ratio = (H1 * W) / (H * W)

        print(f"[DEBUG] Computed: Area = {A}, Velocity = {V:.2f}, Area Ratio = {area_ratio:.4f}")

        # Base coefficient from A13G
        df = data.loc["A13G"]
        df = df[["ANGLE", "A1/A", "C"]].dropna()

        angle_vals = df["ANGLE"].unique()
        angle_match = min([val for val in angle_vals if val >= angle], default=max(angle_vals))

        area_vals = df[df["ANGLE"] == angle_match]["A1/A"].unique()
        area_match = max([val for val in area_vals if val <= area_ratio], default=min(area_vals))

        matched_row = df[(df["ANGLE"] == angle_match) & (df["A1/A"] == area_match)]
        if matched_row.empty:
            return {"Error": "No matching row found for angle and area ratio."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C} (angle = {angle_match}, A1/A = {area_match})")

        # Obstruction correction
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C_screen = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen C = {C_screen}")
            C += C_screen / (area_ratio ** 2)

        vp = (V / 4005) ** 2
        total_loss = C * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss": total_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A13G_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A13G_outputs.output_type = "standard"