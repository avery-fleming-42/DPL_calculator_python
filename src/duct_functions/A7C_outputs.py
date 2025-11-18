import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A7C_outputs(stored_values, *_):
    """
    Calculates the outputs for case A7C using the stored input values, including
    Reynolds Number Correction Factor (RNCF).

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs.
    """
    # Extract required entries
    entry_1 = stored_values.get("entry_1")  # Diameter
    entry_2 = stored_values.get("entry_2")  # Angle (degrees)
    entry_3 = stored_values.get("entry_3")  # Flow Rate

    if not all([entry_1, entry_2, entry_3]):
        return {f"Output {i+1}": None for i in range(4)}

    # Get the relevant data for A7C
    df = get_case_table("A7C")

    # Calculate velocity
    area = math.pi * (entry_1 / 2) ** 2  # Area in square inches
    velocity = entry_3 / (area / 144)  # Velocity in ft/min

    # Calculate Reynolds number and equivalent diameter
    reynolds_number = 8.5 * entry_1 * velocity
    equivalent_diameter = 23766.76 * (velocity ** -1.000794)

    # Determine if RNCF is applicable
    if velocity < (23766.76 / equivalent_diameter):
        # Define correction table
        correction_table = pd.DataFrame(
            {
                "Re_10^4": [1, 2, 3, 4, 6, 8, 10, 14, 20],
                "0.5": [1.40, 1.26, 1.19, 1.14, 1.09, 1.06, 1.04, 1.0, 1.0],
            }
        ).set_index("Re_10^4")

        # Normalize Reynolds number to 10^4 scale
        re_scaled = reynolds_number / 1e4

        # Find the closest Re in the correction table
        closest_re = correction_table.index[
            np.searchsorted(correction_table.index, re_scaled, side="right") - 1
        ]

        rnc_factor = correction_table.loc[closest_re, "0.5"]
    else:
        rnc_factor = 1.0

    # Loss coefficient calculation
    angle_data = df[["ANGLE", "C"]].dropna().sort_values(by="ANGLE")
    closest_angle_row = angle_data.iloc[(angle_data["ANGLE"] - entry_2).abs().argmin()]
    loss_coefficient_base = closest_angle_row["C"]

    # Final calculations
    loss_coefficient = loss_coefficient_base * rnc_factor
    velocity_pressure = (velocity / 4005) ** 2
    pressure_loss = loss_coefficient * velocity_pressure

    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }
