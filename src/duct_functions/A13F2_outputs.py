import math
import pandas as pd

def A13F2_outputs(stored_values, data):
    """
    A13F2 - Round duct exit with varying angle and obstruction type.
    Inputs:
        D (in) - diameter
        angle (deg)
        v (fpm) - reference velocity
        Q_O (cfm) - outlet flow
        obstruction - "none (open)" or "screen"
        n - free area ratio (if obstruction is screen)
    """
    try:
        D = stored_values.get("entry_1")
        angle = stored_values.get("entry_2")
        v = stored_values.get("entry_3")
        Q = stored_values.get("entry_4")
        obstruction = stored_values.get("entry_5")
        n = stored_values.get("entry_6")

        print(f"[DEBUG] Inputs: D={D}, angle={angle}, v={v}, Q={Q}, obstruction={obstruction}, n={n}")

        if None in (D, angle, v, Q):
            return {"Error": "Missing required inputs."}

        A = math.pi * (D / 2) ** 2  # in²
        V = Q / (A / 144)  # ft/min
        vv_ratio = V / v

        print(f"[DEBUG] Computed: Area={A:.2f} in^2, V={V:.2f} fpm, V/V0={vv_ratio:.2f}")

        df = data.loc["A13F2"][["ANGLE", "V/V0", "C"]].dropna()

        # Round down angle
        angle_vals = df["ANGLE"].unique()
        angle_match = max([val for val in angle_vals if val <= angle], default=min(angle_vals))

        # Round up V/V0
        vv_vals = df["V/V0"].unique()
        vv_match = min([val for val in vv_vals if val >= vv_ratio], default=max(vv_vals))

        print(f"[DEBUG] Matching ANGLE={angle_match}, V/V0={vv_match}")

        matched_row = df[(df["ANGLE"] == angle_match) & (df["V/V0"] == vv_match)]
        if matched_row.empty:
            return {"Error": "No matching data found for given angle and V/V0."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        # Screen obstruction correction
        C1 = 0
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"][["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen correction C1 = {C1}")

        # Final pressure loss
        loss_coefficient = C + C1
        vp = (V / 4005) ** 2
        total_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": total_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception in A13F2_outputs: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A13F2_outputs.output_type = "standard"