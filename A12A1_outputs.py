import math
import pandas as pd
import numpy as np

def A12A1_outputs(stored_values, data):
    """
    Calculates the outputs for case A12A1, accounting for:
    - duct geometry (t/D and L/D) for base loss coefficient (C)
    - optional obstruction ("screen" or "perforated plate") with correction factor (C1)
    """

    # Extract inputs
    t = stored_values.get("entry_1")  # duct thickness
    L = stored_values.get("entry_2")  # length
    D = stored_values.get("entry_3")  # diameter
    Q = stored_values.get("entry_4")  # flow rate (cfm)
    obstruction = stored_values.get("entry_5")  # "none", "screen", "perforated plate"
    n = stored_values.get("entry_6")  # free area ratio (if applicable)
    plate_thickness = stored_values.get("entry_7")  # for perforated plate
    hole_diameter = stored_values.get("entry_8")  # for perforated plate

    print("[DEBUG] Inputs:")
    print(f"  t = {t}, L = {L}, D = {D}, Q = {Q}")
    print(f"  obstruction = {obstruction}, n = {n}, plate_thickness = {plate_thickness}, hole_diameter = {hole_diameter}")

    if None in (t, L, D, Q):
        print("[DEBUG] Missing one or more required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = math.pi * (D / 2) ** 2  # in²
        V = Q / (A / 144)  # ft/min

        t_D = t / D
        L_D = L / D
        print(f"[DEBUG] Computed: t/D = {t_D:.4f}, L/D = {L_D:.4f}, Velocity = {V:.2f}")

        # Base loss coefficient C from data
        df = data.loc["A12A1"]
        df = df[["t/D", "L/D", "C"]].dropna()
        tD_vals = df["t/D"].unique()
        LD_vals = df["L/D"].unique()

        tD_match = max([val for val in tD_vals if val <= t_D], default=min(tD_vals))
        LD_match = min([val for val in LD_vals if val >= L_D], default=max(LD_vals))
        print(f"[DEBUG] Matching t/D = {tD_match}, L/D = {LD_match}")

        matched_row = df[(df["t/D"] == tD_match) & (df["L/D"] == LD_match)]
        if matched_row.empty:
            print("[DEBUG] No match found in A12A1 table.")
            return {"Error": "No matching t/D and L/D pair found in data."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        # Obstruction correction
        C1 = 0
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen C1 = {C1}")

        elif obstruction == "perforated plate" and None not in (n, plate_thickness, hole_diameter):
            tD_plate = plate_thickness / hole_diameter
            df_plate = data.loc["A14B1"]
            df_plate = df_plate[["n, free area ratio", "t/D", "C"]].dropna()

            plate_match = df_plate[
                (df_plate["n, free area ratio"] <= n) &
                (df_plate["t/D"] <= tD_plate)
            ]
            if plate_match.empty:
                print("[DEBUG] No match found in A14B1 for perforated plate.")
                return {"Error": "No matching plate correction factor found."}

            n_match = max(plate_match["n, free area ratio"].unique())
            tD_sub = plate_match[plate_match["n, free area ratio"] == n_match]
            tD_match = max(tD_sub["t/D"].unique())
            C1 = tD_sub[tD_sub["t/D"] == tD_match]["C"].values[0]
            print(f"[DEBUG] Perforated Plate C1 = {C1}")

        # Apply final loss coefficient logic
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
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A12A1_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A12A1_outputs.output_type = "standard"
