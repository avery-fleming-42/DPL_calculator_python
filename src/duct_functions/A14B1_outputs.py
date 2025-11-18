import math
import pandas as pd


def A14B1_outputs(stored_values, data):
    """
    Calculates loss coefficient for A14B1: Perforated Plate (round duct)
    Inputs:
    - D: diameter (in)
    - Q: flow rate (cfm)
    - n: free area ratio
    - t_plate: plate thickness (in)
    - d_hole: perforated hole diameter (in)
    """

    D = stored_values.get("entry_1")
    Q = stored_values.get("entry_2")
    n = stored_values.get("entry_3")
    t_plate = stored_values.get("entry_4")
    d_hole = stored_values.get("entry_5")

    print("[DEBUG] Inputs:")
    print(f"  D = {D}, Q = {Q}, n = {n}, t_plate = {t_plate}, d_hole = {d_hole}")

    if None in (D, Q, n, t_plate, d_hole):
        print("[DEBUG] Missing one or more required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # Calculate velocity and velocity pressure
        A = math.pi * (D / 2) ** 2  # Area in in^2
        V = Q / (A / 144)  # ft/min
        vp = (V / 4005) ** 2

        # Determine t/D for perforated plate
        t_D = t_plate / d_hole
        print(f"[DEBUG] Computed t/D = {t_D:.4f}, Velocity = {V:.2f}")

        df = data.loc["A14B1"]
        df = df[["n, free area ratio", "t/D", "C"]].dropna()

        n_vals = df["n, free area ratio"].unique()
        tD_vals = df["t/D"].unique()

        n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
        tD_match = max([val for val in tD_vals if val <= t_D], default=min(tD_vals))

        print(f"[DEBUG] Matching n = {n_match}, t/D = {tD_match}")

        matched_row = df[
            (df["n, free area ratio"] == n_match) &
            (df["t/D"] == tD_match)
        ]

        if matched_row.empty:
            return {"Error": "No matching t/D and n pair found in data."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Loss coefficient C = {C}")

        pressure_loss = C * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A14B1_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }


A14B1_outputs.output_type = "standard"
