import math
import pandas as pd
from data_access import get_case_table


def A12F_outputs(stored_values, *_):
    """
    Calculates outputs for case A12F (conical diverging, round).

    Inputs (stored_values):
        entry_1: L      (length, in)
        entry_2: D      (used in divergence geometry)
        entry_3: Ds     (exit diameter, in)
        entry_4: theta  (included angle, degrees)
        entry_5: Q      (flow rate, cfm)
        entry_6: obstruction ("none" or "screen")
        entry_7: n      (free area ratio, for screen only)

    Returns:
        dict:
            Output 1: Velocity
            Output 2: Velocity Pressure
            Output 3: Loss Coefficient
            Output 4: Pressure Loss
    """
    # Extract inputs
    L      = stored_values.get("entry_1")
    D_geom = stored_values.get("entry_2")  # geometric parameter for divergence
    Ds     = stored_values.get("entry_3")
    theta  = stored_values.get("entry_4")
    Q      = stored_values.get("entry_5")
    obstruction = stored_values.get("entry_6")
    n      = stored_values.get("entry_7")

    if None in (L, D_geom, Ds, theta, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # ==========================
        #   GEOMETRY & VELOCITY
        # ==========================
        theta_rad = math.radians(theta)

        # Upstream diameter from geometry
        D_up = Ds - (2.0 * D_geom) / math.tan(theta_rad / 2.0)
        if D_up <= 0:
            return {"Error": "Invalid geometry: calculated upstream diameter (D_up) is non-positive."}

        # Area and velocity based on upstream section
        A_up = math.pi * (D_up / 2.0) ** 2  # in²
        V = Q / (A_up / 144.0)              # ft/min

        # L/D ratio for table
        L_D = L / D_up

        # ==========================
        #   BASE COEFFICIENT (A12F)
        # ==========================
        df = get_case_table("A12F")
        df = df[["L/D", "ANGLE", "C"]].dropna()

        LD_vals = df["L/D"].unique()
        # Round L/D down to nearest tabulated value (or min if below range)
        LD_match = max(
            [val for val in LD_vals if val <= L_D],
            default=min(LD_vals),
        )

        matched_row = df[(df["L/D"] == LD_match) & (df["ANGLE"] == theta)]
        if matched_row.empty:
            return {"Error": "No matching L/D and ANGLE pair found in A12F."}

        C = matched_row["C"].values[0]

        # ==========================
        #   SCREEN CORRECTION (A14A1)
        # ==========================
        if obstruction == "screen" and n is not None:
            df_screen = get_case_table("A14A1")
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()

            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max(
                [val for val in n_vals if val <= n],
                default=min(n_vals),
            )
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            # As from Ds, A from D_up
            A_s = math.pi * (Ds / 2.0) ** 2
            As_A_ratio = A_s / A_up

            loss_coefficient = C + (C1 / (As_A_ratio ** 2))
        else:
            loss_coefficient = C

        # ==========================
        #   OUTPUTS
        # ==========================
        vp = (V / 4005.0) ** 2
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
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


A12F_outputs.output_type = "standard"
