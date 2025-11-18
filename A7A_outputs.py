import math
import pandas as pd
import numpy as np

def A7A_outputs(stored_values, data):
    """
    Calculates the outputs for case A7A using the stored input values, including
    Reynolds Number Correction Factor (RNCF).

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs.
    """
    # Extract required entries from stored values
    entry_1 = stored_values.get("entry_1")  # Diameter
    entry_2 = stored_values.get("entry_2")  # R/D value
    entry_3 = stored_values.get("entry_3")  # Angle for A7_k
    entry_4 = stored_values.get("entry_4")  # Flow rate

    # Ensure all required inputs are available
    if entry_1 is None or entry_2 is None or entry_3 is None or entry_4 is None:
        return {
            "Output 1: Velocity": None,
            "Output 2: Vel. Pres @ V0 (in w.c.)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss (in w.c.)": None,
        }

    # Get the relevant data for A7A
    df = data.loc["A7A"]  # Assuming data contains data specific to A7A

    # Calculate velocity
    area = math.pi * (entry_1 / 2) ** 2  # Cross-sectional area in square inches
    velocity = entry_4 / (area / 144)  # Velocity in ft/min

    # Calculate correction factor (A7_k) based on angle
    df_angle = df[["ANGLE", "K"]].dropna()
    df_angle = df_angle.sort_values(by="ANGLE")
    closest_angle_row = df_angle[df_angle["ANGLE"] >= entry_3].iloc[0]
    correction_factor = closest_angle_row["K"]

    # Calculate base loss coefficient (A7A_C) based on R/D
    df_rd = df[["R/D", "C"]].dropna()
    df_rd = df_rd.sort_values(by="R/D")
    valid_rows = df_rd[df_rd["R/D"] <= entry_2]
    closest_rd_row = valid_rows.iloc[-1]
    loss_coefficient_base = closest_rd_row["C"]

    # Calculate Reynolds Number Correction Factor (RNCF)
    reynolds_number = 8.5 * entry_1 * velocity
    equivalent_diameter = 23766.76 * (velocity ** -1.000794)

    if velocity < (23766.76 / equivalent_diameter):
        # Define correction table
        correction_table = pd.DataFrame(
            {
                "Re_10^4": [1, 2, 3, 4, 6, 8, 10, 14, 20],
                "0.5": [1.40, 1.26, 1.19, 1.14, 1.09, 1.06, 1.04, 1.0, 1.0],
                "0.75": [1.77, 1.64, 1.56, 1.46, 1.38, 1.30, 1.15, 1.0, 1.0],
            }
        ).set_index("Re_10^4")

        # Normalize Reynolds number to 10^4 scale
        re_scaled = reynolds_number / 1e4

        # Find the closest R/D column
        r_d_rounded = "0.5" if entry_2 <= 0.5 else "0.75"

        # Find the closest Re in the correction table
        closest_re = correction_table.index[
            np.searchsorted(correction_table.index, re_scaled, side="right") - 1
        ]

        rnc_factor = correction_table.loc[closest_re, r_d_rounded]
    else:
        rnc_factor = 1.0

    # Calculate combined loss coefficient
    loss_coefficient = loss_coefficient_base * correction_factor * rnc_factor

    # Calculate velocity pressure
    velocity_pressure = (velocity / 4005) ** 2

    # Calculate pressure loss
    pressure_loss = loss_coefficient * velocity_pressure

    # Return results as a dictionary
    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }