import math
import pandas as pd
from data_access import get_case_table


def A13A_outputs(stored_values, *_):
    """
    Outputs for A13A (exit, round conical).

    Inputs (stored_values):
        entry_1: L   (length, in)
        entry_2: D   (small-end diameter, in)
        entry_3: Ds  (exit diameter, in)
        entry_4: θ   (divergence angle, degrees)
        entry_5: Q   (flow rate, cfm)
        entry_6: obstruction ("none", "screen", etc.)
        entry_7: n   (free area ratio, only if obstruction == "screen")

    Returns:
        dict with:
            Output 1: Velocity
            Output 2: Velocity Pressure
            Output 3: Loss Coefficient
            Output 4: Pressure Loss
            (optional "Error" key on failure)
    """
    # Extract inputs
    L = stored_values.get("entry_1")   # Length (in)
    D = stored_values.get("entry_2")   # Small-end diameter (in)
    Ds = stored_values.get("entry_3")  # Exit diameter (in)
    theta = stored_values.get("entry_4")  # Divergence angle (deg)
    Q = stored_values.get("entry_5")   # Flow rate (cfm)
    obstruction = stored_values.get("entry_6")
    n = stored_values.get("entry_7")

    # Basic validation
    if None in (L, D, Ds, theta, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": "Missing one or more required inputs.",
        }

    try:
        # -----------------------------
        #  Geometry & Velocity
        # -----------------------------
        # Area at small end (A) and exit (A1), in²
        A = math.pi * (D / 2.0) ** 2
        A1 = math.pi * (Ds / 2.0) ** 2

        # Velocity based on A (ft/min)
        V = Q / (A / 144.0)

        # L/D ratio
        LD = L / D

        # -----------------------------
        #  Base loss coefficient from A13A
        # -----------------------------
        df = get_case_table("A13A")
        df = df[["L/D", "ANGLE", "C"]].dropna()

        LD_vals = df["L/D"].unique()
        # Choose the largest tabulated L/D <= actual, fallback to min
        LD_match = max([val for val in LD_vals if val <= LD], default=min(LD_vals))

        matched_row = df[(df["L/D"] == LD_match) & (df["ANGLE"] == theta)]
        if matched_row.empty:
            return {"Error": "No match found for provided L/D and angle in A13A."}

        C_base = matched_row["C"].values[0]

        # -----------------------------
        #  Screen correction (A14A1)
        # -----------------------------
        C_total = C_base
        if obstruction is not None and isinstance(obstruction, str):
            if obstruction.strip().lower() == "screen" and n is not None:
                df_screen = get_case_table("A14A1")
                df_screen = df_screen[["n, free area ratio", "C"]].dropna()

                n_vals = df_screen["n, free area ratio"].unique()
                n_match = max(
                    [val for val in n_vals if val <= n],
                    default=min(n_vals),
                )
                C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

                # As is at exit (A1) with screen
                As_A_ratio = A1 / A if A > 0 else 1.0
                C_total = C_base + (C1 / (As_A_ratio ** 2))

        # -----------------------------
        #  Final outputs
        # -----------------------------
        vp = (V / 4005.0) ** 2
        pressure_loss = C_total * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": C_total,
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


A13A_outputs.output_type = "standard"
