import math
import pandas as pd

def A12G_outputs(stored_values, data):
    """
    Calculates outputs for case A12G:
    - Handles both round and rectangular hood profiles
    - Supports optional screen correction
    """

    profile = stored_values.get("entry_1")  # "round hood" or "square or rectangular hood"

    try:
        # Extract profile-specific values
        if profile == "round hood":
            D1 = stored_values.get("entry_2")
            D = stored_values.get("entry_3")
            angle = stored_values.get("entry_4")
            Q = stored_values.get("entry_5")
            obstruction = stored_values.get("entry_6")
            n = stored_values.get("entry_7")
        else:
            H1 = stored_values.get("entry_2")
            W1 = stored_values.get("entry_3")
            D = stored_values.get("entry_4")
            angle = stored_values.get("entry_5")
            Q = stored_values.get("entry_6")
            obstruction = stored_values.get("entry_7")
            n = stored_values.get("entry_8")

        # Common downstream area
        A = math.pi * (D / 2) ** 2
        V = Q / (A / 144)

        # Determine A1 based on profile
        if profile == "round hood":
            A1 = math.pi * (D1 / 2) ** 2
        else:
            A1 = H1 * W1

        print(f"[DEBUG] Profile: {profile}, Angle: {angle}, Obstruction: {obstruction}")
        print(f"[DEBUG] A1 = {A1:.2f}, A = {A:.2f}, V = {V:.2f}")

        # Filter data by A12G, config, and angle
        df = data.loc["A12G"]
        config_key = "round hood" if profile == "round hood" else "rect hood"
        df = df[(df["configuration"].str.lower() == config_key.lower()) &
                (df["ANGLE"] == angle)]

        if df.empty:
            return {"Error": "No matching data found for A12G configuration and angle."}

        C = df.iloc[0]["C"]
        print(f"[DEBUG] Base coefficient C = {C}")

        # Optional screen correction
        C1 = 0
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            area_ratio_sq = (A1 / A) ** 2 if A != 0 else 1
            C += (C1 / area_ratio_sq)
            print(f"[DEBUG] Screen C1 = {C1}, A1/A = {A1 / A:.3f}, Adjusted C = {C:.3f}")

        # Final outputs
        vp = (V / 4005) ** 2
        pressure_loss = C * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A12G_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A12G_outputs.output_type = "standard"
