import math
import pandas as pd
from data_access import get_case_table


def A12E2_outputs(stored_values, *_):
    """
    Calculates outputs for case A12E2 (rectangular conical bellmouth with end wall).

    Inputs (stored_values):
        entry_1: L   (length, in)
        entry_2: H   (entry height, in)
        entry_3: W   (entry width, in)
        entry_4: Hs  (exit height, in)
        entry_5: Ws  (exit width, in)
        entry_6: Q   (flow rate, cfm)
        entry_7: obstruction ("none" or "screen")
        entry_8: n   (free area ratio, for screen)

    Returns:
        dict with:
            Output 1: Velocity
            Output 2: Velocity Pressure
            Output 3: Loss Coefficient
            Output 4: Pressure Loss
    """
    # Extract inputs
    L  = stored_values.get("entry_1")
    H  = stored_values.get("entry_2")
    W  = stored_values.get("entry_3")
    Hs = stored_values.get("entry_4")
    Ws = stored_values.get("entry_5")
    Q  = stored_values.get("entry_6")
    obstruction = stored_values.get("entry_7")
    n  = stored_values.get("entry_8")

    if None in (L, H, W, Hs, Ws, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        # ==========================
        #   EQUIVALENT DIAMETERS
        # ==========================
        # Entry/exit equivalent diameters (in)
        D1 = 1.0 / (2.0 * (H + W)  / (H  * W))
        D2 = 1.0 / (2.0 * (Hs + Ws) / (Hs * Ws))

        # Use circular-equivalent area based on D1
        A = math.pi * (D1 / 2.0) ** 2  # in²
        V = Q / (A / 144.0)            # ft/min

        # Included angle from D1 → D2
        angle = 2.0 * math.degrees(math.atan((D2 - D1) / (2.0 * L)))
        angle_rounded = round(angle)

        # L/D based on D1
        L_D = L / D1

        # ==========================
        #   BASE COEFFICIENT (A12E2)
        # ==========================
        df = get_case_table("A12E2")
        df = df[["L/D", "ANGLE", "C"]].dropna()

        LD_vals  = df["L/D"].unique()
        ANG_vals = df["ANGLE"].unique()

        # L/D: round down to nearest table value (or min if below)
        LD_match = max(
            [val for val in LD_vals if val <= L_D],
            default=min(LD_vals),
        )
        # ANGLE: nearest table angle
        ANG_match = min(ANG_vals, key=lambda x: abs(x - angle_rounded))

        matched_row = df[(df["L/D"] == LD_match) & (df["ANGLE"] == ANG_match)]
        if matched_row.empty:
            return {"Error": "No match found in A12E2 table for L/D and ANGLE."}

        C = matched_row["C"].values[0]

        # ==========================
        #   SCREEN CORRECTION (A14A1)
        # ==========================
        if obstruction == "screen" and n is not None:
            df_screen = get_case_table("A14A1")
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()

            # Largest table n ≤ actual n, or smallest if below range
            n_match = max(
                [val for val in n_vals if val <= n],
                default=min(n_vals),
            )
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]

            # As/A = n for a uniform screen
            As_A = n
            loss_coefficient = C + (C1 / (As_A ** 2))
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


A12E2_outputs.output_type = "standard"
