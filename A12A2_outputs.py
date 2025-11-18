import math
import pandas as pd
import numpy as np

def A12A2_outputs(stored_values, data):
    """
    Calculates outputs for case A12A2 (rectangular duct entry), accounting for:
    - duct geometry (t/D and L/D based on equivalent diameter)
    - optional obstruction ("screen" or "perforated plate") with correction factor (C1)
    """

    # Extract inputs
    t = stored_values.get("entry_1")  # duct thickness
    L = stored_values.get("entry_2")  # length
    H = stored_values.get("entry_3")  # height
    W = stored_values.get("entry_4")  # width
    Q = stored_values.get("entry_5")  # flow rate (cfm)
    obstruction = stored_values.get("entry_6")  # "none", "screen", "perforated plate"
    n = stored_values.get("entry_7")  # free area ratio (if applicable)
    plate_thickness = stored_values.get("entry_8")  # only for perforated plate
    hole_diameter = stored_values.get("entry_9")    # only for perforated plate

    print("[DEBUG] Inputs:")
    print(f"  t = {t}, L = {L}, H = {H}, W = {W}, Q = {Q}")
    print(f"  obstruction = {obstruction}, n = {n}, plate_t = {plate_thickness}, hole_d = {hole_diameter}")

    if None in (t, L, H, W, Q):
        print("[DEBUG] Missing one or more required duct inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = H * W  # in²
        D_equiv = 1 / (2 * (H + W) / (H * W))  # in
        V = Q / (A / 144)  # ft/min

        t_D = t / D_equiv
        L_D = L / D_equiv

        print(f"[DEBUG] D_equiv = {D_equiv:.4f}, t/D = {t_D:.4f}, L/D = {L_D:.4f}, Velocity = {V:.2f}")

        df = data.loc["A12A2"]
        df = df[["t/D", "L/D", "C"]].dropna()

        tD_match = max([val for val in df["t/D"].unique() if val <= t_D], default=min(df["t/D"]))
        LD_match = min([val for val in df["L/D"].unique() if val >= L_D], default=max(df["L/D"]))

        print(f"[DEBUG] Matching t/D = {tD_match}, L/D = {LD_match}")
        matched_row = df[(df["t/D"] == tD_match) & (df["L/D"] == LD_match)]
        if matched_row.empty:
            return {"Error": "No matching t/D and L/D pair found in data."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        C1 = 0
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_match = max([val for val in df_screen["n, free area ratio"].unique() if val <= n], default=min(df_screen["n, free area ratio"]))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen C1 = {C1}")

        elif obstruction == "perforated plate" and None not in (n, plate_thickness, hole_diameter):
            plate_t_D = plate_thickness / hole_diameter
            df_plate = data.loc["A14B1"]
            df_plate = df_plate[["n, free area ratio", "t/D", "C"]].dropna()

            match = df_plate[
                (df_plate["n, free area ratio"] <= n) &
                (df_plate["t/D"] <= plate_t_D)
            ]

            if match.empty:
                return {"Error": "No matching perforated plate correction."}

            n_match = max(match["n, free area ratio"].unique())
            tD_sub = match[match["n, free area ratio"] == n_match]
            tD_match = max(tD_sub["t/D"].unique())
            C1 = tD_sub[tD_sub["t/D"] == tD_match]["C"].values[0]
            print(f"[DEBUG] Perforated Plate C1 = {C1}")

        if obstruction in ("screen", "perforated plate"):
            if t_D <= 0.05:
                loss_coefficient = 1 + C1
                print("[DEBUG] Using 1 + C1 for total loss coefficient")
            else:
                loss_coefficient = C + C1
                print("[DEBUG] Using C + C1 for total loss coefficient")
        else:
            loss_coefficient = C
            print("[DEBUG] No obstruction: using base C only")

        vp = (V / 4005) ** 2
        total_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": total_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A12A2_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A12A2_outputs.output_type = "standard"
