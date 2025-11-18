import math
import pandas as pd

def A12E2_outputs(stored_values, data):
    """
    Calculates outputs for case A12E2 (rectangular conical bellmouth, with end wall).
    Inputs:
    - L, H, W, Hs, Ws, Q, obstruction, and optional n for screen
    """

    # Extract inputs
    L = stored_values.get("entry_1")  # Length
    H = stored_values.get("entry_2")  # Height
    W = stored_values.get("entry_3")  # Width
    Hs = stored_values.get("entry_4")  # Exit Height
    Ws = stored_values.get("entry_5")  # Exit Width
    Q = stored_values.get("entry_6")  # Flow rate (cfm)
    obstruction = stored_values.get("entry_7")  # "none" or "screen"
    n = stored_values.get("entry_8")  # Free area ratio

    print("[DEBUG] Inputs:")
    print(f"  L = {L}, H = {H}, W = {W}, Hs = {Hs}, Ws = {Ws}, Q = {Q}")
    print(f"  obstruction = {obstruction}, n = {n}")

    if None in (L, H, W, Hs, Ws, Q):
        print("[DEBUG] Missing one or more required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # Compute inlet and outlet equivalent diameters
        D1 = 1 / (2 * (H + W) / (H * W))
        D2 = 1 / (2 * (Hs + Ws) / (Hs * Ws))

        A = math.pi * (D1 / 2) ** 2  # Area in in² (converted from rectangular)
        V = Q / (A / 144)  # ft/min

        # Calculate angle
        angle = 2 * math.degrees(math.atan((D2 - D1) / (2 * L)))
        angle_rounded = round(angle)
        print(f"[DEBUG] D1 = {D1:.4f}, D2 = {D2:.4f}, Velocity = {V:.2f}, Angle = {angle:.2f}")

        # Calculate L/D
        L_D = L / D1
        print(f"[DEBUG] L/D = {L_D:.4f}")

        # Lookup base coefficient
        df = data.loc["A12E2"]
        df = df[["L/D", "ANGLE", "C"]].dropna()

        # Find match: L/D round down, ANGLE nearest
        LD_vals = df["L/D"].unique()
        ANG_vals = df["ANGLE"].unique()

        LD_match = max([val for val in LD_vals if val <= L_D], default=min(LD_vals))
        ANG_match = min(ANG_vals, key=lambda x: abs(x - angle_rounded))

        matched_row = df[(df["L/D"] == LD_match) & (df["ANGLE"] == ANG_match)]
        if matched_row.empty:
            return {"Error": "No match found in A12E2 table."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        # Handle screen obstruction
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            As_A = n
            loss_coefficient = C + (C1 / As_A ** 2)
            print(f"[DEBUG] Screen C1 = {C1}, Adjusted Loss Coefficient = {loss_coefficient}")
        else:
            loss_coefficient = C
            print("[DEBUG] No obstruction: using base C only")

        # Calculate final outputs
        vp = (V / 4005) ** 2
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A12E2_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A12E2_outputs.output_type = "standard"