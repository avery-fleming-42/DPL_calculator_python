import math
import pandas as pd

def A12F_outputs(stored_values, data):
    """
    Calculates outputs for case A12F (conical diverging, round).
    Inputs:
    - L, D, Ds, θ, Q, obstruction, and optional n (screen only)
    """

    # Extract inputs
    L = stored_values.get("entry_1")  # Length
    D = stored_values.get("entry_2")  # D (used in divergence)
    Ds = stored_values.get("entry_3")  # Exit diameter
    theta = stored_values.get("entry_4")  # Angle in degrees
    Q = stored_values.get("entry_5")  # Flow rate (cfm)
    obstruction = stored_values.get("entry_6")  # Obstruction type
    n = stored_values.get("entry_7")  # Free area ratio (for screen)

    print("[DEBUG] Inputs:")
    print(f"  L = {L}, D = {D}, Ds = {Ds}, θ = {theta}, Q = {Q}")
    print(f"  obstruction = {obstruction}, n = {n}")

    if None in (L, D, Ds, theta, Q):
        print("[DEBUG] Missing one or more required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # Convert θ to radians for tan()
        theta_rad = math.radians(theta)

        # Calculate upstream diameter
        D_up = Ds - (2 * D) / math.tan(theta_rad / 2)
        if D_up <= 0:
            return {"Error": "Invalid geometry: calculated D_up is non-positive."}

        # Area and velocity
        A = math.pi * (D_up / 2) ** 2  # in²
        V = Q / (A / 144)  # ft/min

        # L/D ratio
        L_D = L / D_up
        print(f"[DEBUG] Calculated D_up = {D_up:.2f}, L/D = {L_D:.4f}, Velocity = {V:.2f}")

        # Base coefficient from A12F table
        df = data.loc["A12F"]
        df = df[["L/D", "ANGLE", "C"]].dropna()

        LD_vals = df["L/D"].unique()
        LD_match = max([val for val in LD_vals if val <= L_D], default=min(LD_vals))
        matched_row = df[(df["L/D"] == LD_match) & (df["ANGLE"] == theta)]

        if matched_row.empty:
            print("[DEBUG] No match found in A12F table.")
            return {"Error": "No matching L/D and angle pair found."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        # Screen obstruction correction (no perforated plate allowed for A12F)
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            # A from D_up, As from Ds
            A_up = math.pi * (D_up / 2) ** 2
            A_s = math.pi * (Ds / 2) ** 2
            As_A_ratio = A_s / A_up

            loss_coefficient = C + (C1 / (As_A_ratio ** 2))
            print(f"[DEBUG] Screen C1 = {C1}, As/A = {As_A_ratio:.3f}, Adjusted C = {loss_coefficient:.3f}")
        else:
            loss_coefficient = C
            print("[DEBUG] No screen selected, using base C only")

        vp = (V / 4005) ** 2
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A12F_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A12F_outputs.output_type = "standard"