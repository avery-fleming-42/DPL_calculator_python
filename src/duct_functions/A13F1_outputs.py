import math
import pandas as pd

def A13F1_outputs(stored_values, data):
    H = stored_values.get("entry_1")
    W = stored_values.get("entry_2")
    angle = stored_values.get("entry_3")
    v_ref = stored_values.get("entry_4")  # reference velocity (fps)
    Q = stored_values.get("entry_5")  # flow rate (cfm)
    obstruction = stored_values.get("entry_6")
    n = stored_values.get("entry_7")  # free area ratio (if applicable)

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, W = {W}, angle = {angle}, v_ref = {v_ref}, Q = {Q}, obstruction = {obstruction}, n = {n}")

    if None in (H, W, angle, v_ref, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Ratio (V/V0)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = H * W  # in^2
        V = Q / (A / 144)  # ft/min
        V_fps = V / 60  # convert to fps
        V_V0 = V_fps / v_ref

        aspect_ratio = H / W
        print(f"[DEBUG] Area = {A:.2f} in^2, Velocity = {V:.2f} fpm ({V_fps:.2f} fps), V/V0 = {V_V0:.2f}, Aspect Ratio = {aspect_ratio:.2f}")

        df = data.loc["A13F1"][["H/W", "ANGLE", "V/V0", "C"]].dropna()

        if aspect_ratio <= 0.2:
            df_filtered = df[df["H/W"] == "0.1-0.2"]
        elif aspect_ratio <= 2.0:
            df_filtered = df[df["H/W"] == "0.5-2.0"]
        else:
            df_filtered = df[df["H/W"] == "5-10"]

        angle_vals = df_filtered["ANGLE"].unique()
        VV_vals = df_filtered["V/V0"].unique()

        angle_match = max([val for val in angle_vals if val <= angle], default=min(angle_vals))
        VV_match = min([val for val in VV_vals if val >= V_V0], default=max(VV_vals))

        print(f"[DEBUG] Matched Angle = {angle_match}, V/V0 = {VV_match}")

        matched_row = df_filtered[(df_filtered["ANGLE"] == angle_match) & (df_filtered["V/V0"] == VV_match)]
        if matched_row.empty:
            return {"Error": "No matching row found in A13F1 data."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base Coefficient C = {C}")

        C_total = C
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            A_s = A  # flow area
            total_area = A  # assuming screen is same size as duct opening
            obstruction_correction = C1 / ((A_s / total_area) ** 2)
            C_total += obstruction_correction
            print(f"[DEBUG] Screen C1 = {C1}, Total C = {C_total}")

        vp = (V / 4005) ** 2
        pressure_loss = C_total * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Ratio (V/V0)": V_V0,
            "Output 3: Loss Coefficient": C_total,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A13F1_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Ratio (V/V0)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A13F1_outputs.output_type = "standard"