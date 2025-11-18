import math
import pandas as pd

def A13D_outputs(stored_values, data):
    """
    Calculates outputs for case A13D (rectangular exit transition with potentially different vertical and lateral angles).
    Inputs:
    - H, W: initial dimensions (in)
    - H_1, W_1: final dimensions (in)
    - L: transition length (in)
    - Q: flow rate (cfm)
    - obstruction: 'none (open)' or 'screen'
    - n: optional, free area ratio if screen is selected
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
            return {f"Output {i + 1}": None for i in range(4)}

        A = H * W
        A_s = H_1 * W_1
        area_ratio = A_s / A

        V = Q / (A / 144)  # ft/min
        vp = (V / 4005) ** 2

        # Compute angles in degrees
        lateral_angle = math.degrees(2 * math.atan((W_1 - W) / (2 * L)))
        vertical_angle = math.degrees(2 * math.atan((H_1 - H) / (2 * L)))
        angle = max(lateral_angle, vertical_angle)

        print(f"[DEBUG] Lateral Angle: {lateral_angle:.2f}, Vertical Angle: {vertical_angle:.2f}, Used Angle: {angle:.2f}")

        # Round angle
        angle_col = "ANGLE"
        if angle <= 30:
            angle_rounded = max([a for a in data.loc["A13D"][angle_col].unique() if a <= angle], default=min(data.loc["A13D"][angle_col]))
        else:
            angle_rounded = min([a for a in data.loc["A13D"][angle_col].unique() if a >= angle], default=max(data.loc["A13D"][angle_col]))

        # Round area ratio down
        ar_col = "As/A"
        area_vals = data.loc["A13D"][ar_col].unique()
        ar_rounded = max([v for v in area_vals if v <= area_ratio], default=min(area_vals))

        df = data.loc["A13D"]
        df = df[(df[angle_col] == angle_rounded) & (df[ar_col] == ar_rounded)]

        if df.empty:
            return {"Error": "No matching loss coefficient found."}

        C = df["C"].values[0]
        print(f"[DEBUG] Matched C = {C} at ANGLE = {angle_rounded}, As/A = {ar_rounded}")

        # Obstruction correction
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen C1 = {C1}")

            total_loss_coefficient = C + (C1 / (A_s / A) ** 2)
            print(f"[DEBUG] Final Loss Coefficient with screen = {total_loss_coefficient:.4f}")
        else:
            total_loss_coefficient = C
            print(f"[DEBUG] Final Loss Coefficient (no screen) = {total_loss_coefficient:.4f}")

        pressure_loss = total_loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": total_loss_coefficient,
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

A13D_outputs.output_type = "standard"