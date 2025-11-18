import math
import pandas as pd

def A13B_outputs(stored_values, data):
    """
    Calculates outputs for case A13B (conical exit with/without wall), accounting for:
    - Base loss coefficient from angle and As/A ratio
    - Optional screen obstruction correction
    """

    # Extract inputs
    L = stored_values.get("entry_1")
    D = stored_values.get("entry_2")
    Ds = stored_values.get("entry_3")
    Q = stored_values.get("entry_4")
    obstruction = stored_values.get("entry_5")
    n = stored_values.get("entry_6")  # Only for screen

    print("[DEBUG] Inputs:")
    print(f"  L = {L}, D = {D}, Ds = {Ds}, Q = {Q}, obstruction = {obstruction}, n = {n}")

    if None in (L, D, Ds, Q):
        print("[DEBUG] Missing required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = math.pi * (D / 2) ** 2
        As = math.pi * (Ds / 2) ** 2
        A_ratio = As / A

        angle = math.degrees(2 * math.atan((Ds - D) / (2 * L)))
        print(f"[DEBUG] Angle = {angle:.2f} degrees, A_ratio = {A_ratio:.4f}")

        # Get base loss coefficient from A13B data
        df = data.loc["A13B"][["ANGLE", "As/A", "C"]].dropna()

        angle_vals = sorted(df["ANGLE"].unique())
        A_ratio_vals = sorted(df["As/A"].unique())

        angle_match = min([val for val in angle_vals if val >= angle], default=max(angle_vals))

        if angle < 45:
            A_ratio_match = max([val for val in A_ratio_vals if val <= A_ratio], default=min(A_ratio_vals))
        else:
            A_ratio_match = min(A_ratio_vals, key=lambda x: abs(x - A_ratio))

        print(f"[DEBUG] Matched angle = {angle_match}, As/A = {A_ratio_match}")

        matched_row = df[(df["ANGLE"] == angle_match) & (df["As/A"] == A_ratio_match)]
        if matched_row.empty:
            return {"Error": "No matching angle and As/A pair found in data."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        # Screen correction
        C1 = 0
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"][["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen correction C1 = {C1}")

        loss_coefficient = C + (C1 / (A_ratio ** 2)) if obstruction == "screen" else C
        print(f"[DEBUG] Final loss coefficient = {loss_coefficient}")

        V = Q / (A / 144)  # ft/min
        vp = (V / 4005) ** 2
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A13B_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A13B_outputs.output_type = "standard"