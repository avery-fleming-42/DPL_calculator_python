import math
import pandas as pd
import numpy as np

def A7B_outputs(stored_values, data):
    """
    Calculates the outputs for case A7B using the stored input values, including
    Reynolds Number Correction Factor (RNCF).
    """

    # Extract required entries
    entry_1 = stored_values.get("entry_1")  # Diameter
    entry_2 = stored_values.get("entry_2")  # R/D value
    entry_3 = stored_values.get("entry_3")  # Number of pieces
    entry_4 = stored_values.get("entry_4")  # Flow rate

    # Validate inputs
    if entry_1 is None or entry_2 is None or entry_3 is None or entry_4 is None:
        return {
            "Output 1: Velocity": None,
            "Output 2: Vel. Pres @ V0 (in w.c.)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss (in w.c.)": None,
        }

    # Get A7B-specific data
    df = data.loc["A7B"]

    # Calculate velocity
    area = math.pi * (entry_1 / 2) ** 2  # Cross-sectional area in square inches
    velocity = entry_4 / (area / 144)    # Velocity in ft/min

    # Calculate Reynolds Number Correction Factor (RNCF)
    reynolds_number = 8.5 * entry_1 * velocity
    equivalent_diameter = 23766.76 * (velocity ** -1.000794)

    if velocity < (23766.76 / equivalent_diameter):
        correction_table = pd.DataFrame(
            {
                "Re_10^4": [1, 2, 3, 4, 6, 8, 10, 14, 20],
                "0.5": [1.40, 1.26, 1.19, 1.14, 1.09, 1.06, 1.04, 1.0, 1.0],
                "0.75": [1.77, 1.64, 1.56, 1.46, 1.38, 1.30, 1.15, 1.0, 1.0],
            }
        ).set_index("Re_10^4")

        re_scaled = reynolds_number / 1e4
        r_d_rounded = "0.5" if entry_2 <= 0.5 else "0.75"

        closest_re = correction_table.index[
            np.searchsorted(correction_table.index, re_scaled, side="right") - 1
        ]
        rnc_factor = correction_table.loc[closest_re, r_d_rounded]
    else:
        rnc_factor = 1.0

    # Find closest R/D and #pieces in table
    df_rd_pieces = df[["R/D", "# pieces", "C"]].dropna().sort_values(by=["R/D", "# pieces"])

    valid_rd_rows = df_rd_pieces[df_rd_pieces["R/D"] <= entry_2]
    if valid_rd_rows.empty:
        raise ValueError(f"No valid R/D value less than or equal to {entry_2}")
    closest_rd_row = valid_rd_rows.iloc[-1]

    valid_pieces_rows = valid_rd_rows[valid_rd_rows["# pieces"] <= entry_3]
    if valid_pieces_rows.empty:
        raise ValueError(f"No valid # pieces value less than or equal to {entry_3}")
    closest_pieces_row = valid_pieces_rows.iloc[-1]

    loss_coefficient_base = closest_pieces_row["C"]

    # Final coefficient with RNCF
    loss_coefficient = loss_coefficient_base * rnc_factor

    # Velocity pressure
    velocity_pressure = (velocity / 4005) ** 2

    # Pressure loss
    pressure_loss = loss_coefficient * velocity_pressure

    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }
