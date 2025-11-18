import math
import pandas as pd

def A13A_outputs(stored_values, data):
    """
    Outputs for A13A (exit, round conical).
    Inputs: L, D, Ds, angle, Q, obstruction, and optional n (if screen).
    """

    # Extract inputs
    L = stored_values.get("entry_1")  # Length
    D = stored_values.get("entry_2")  # Small end diameter
    Ds = stored_values.get("entry_3")  # Exit diameter
    theta = stored_values.get("entry_4")  # Divergence angle (degrees)
    Q = stored_values.get("entry_5")  # Flow rate (cfm)
    obstruction = stored_values.get("entry_6")  # "none", "screen"
    n = stored_values.get("entry_7")  # Free area ratio if obstruction is screen

    print("[DEBUG] Inputs:")
    print(f"  L = {L}, D = {D}, Ds = {Ds}, angle = {theta}, Q = {Q}, obstruction = {obstruction}, n = {n}")

    if None in (L, D, Ds, theta, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": "Missing one or more required inputs."
        }

    try:
        # Area A from D (in²), Area A₁ from Ds (in²)
        A = math.pi * (D / 2) ** 2
        A1 = math.pi * (Ds / 2) ** 2

        # Velocity (ft/min)
        V = Q / (A / 144)

        # L/D ratio for matching
        LD = L / D
        df = data.loc["A13A"]
        df = df[["L/D", "ANGLE", "C"]].dropna()

        LD_vals = df["L/D"].unique()
        LD_match = max([val for val in LD_vals if val <= LD], default=min(LD_vals))

        matched_row = df[(df["L/D"] == LD_match) & (df["ANGLE"] == theta)]

        if matched_row.empty:
            return {"Error": "No match found for provided L/D and angle."}

        C_base = matched_row["C"].values[0]
        print(f"[DEBUG] Base C = {C_base}")

        # Screen correction from A14A1 if obstruction is screen
        if obstruction.strip().lower() == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            As_A_ratio = A1 / A
            C_total = C_base + (C1 / (As_A_ratio ** 2))
            print(f"[DEBUG] Screen C1 = {C1}, As/A = {As_A_ratio:.3f}, Adjusted C = {C_total}")
        else:
            C_total = C_base

        vp = (V / 4005) ** 2
        pressure_loss = C_total * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C_total,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] A13A_outputs exception: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A13A_outputs.output_type = "standard"
