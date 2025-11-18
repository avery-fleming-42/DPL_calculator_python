import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A7D_outputs(stored_values, *_):
    """
    Calculates the outputs for case A7D using the stored input values, including
    Reynolds Number Correction Factor (RNCF).

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs.
    """
    # Extract required entries
    entry_1 = stored_values.get("entry_1")  # Height
    entry_2 = stored_values.get("entry_2")  # Width
    entry_3 = stored_values.get("entry_3")  # Angle
    entry_4 = stored_values.get("entry_4")  # Flow Rate

    # Validate inputs
    if not all([entry_1, entry_2, entry_3, entry_4]):
        return {f"Output {i+1}": None for i in range(4)}

    # Get the relevant data for A7D
    df = get_case_table("A7D")

    # Calculate velocity
    area = (entry_1 * entry_2) / 144  # Area in square feet
    velocity = entry_4 / area  # Velocity in ft/min

    # Calculate Reynolds number and equivalent diameter
    hydraulic_diameter = 2 * (entry_1 * entry_2) / (entry_1 + entry_2)  # ft
    reynolds_number = 8.5 * hydraulic_diameter * velocity
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

    # Determine H/W ratio and Angle
    h_w_ratio = entry_1 / entry_2

    # H/W matching
    if "H/W" not in df.columns or "ANGLE" not in df.columns or "C" not in df.columns:
        raise KeyError("Data for A7D must include 'H/W', 'ANGLE', and 'C' columns.")
    hw_data = df[["H/W", "ANGLE", "C"]].dropna().sort_values(by=["H/W", "ANGLE"])

    # Find closest H/W less than or equal to h_w_ratio
    valid_hw = hw_data[hw_data["H/W"] <= h_w_ratio]
    if valid_hw.empty:
        closest_hw_row = hw_data.iloc[0]  # Use the smallest H/W if none match
    else:
        closest_hw_row = valid_hw.iloc[-1]  # Use the largest H/W less than or equal to h_w_ratio

    closest_h_w = closest_hw_row["H/W"]

    # Find closest Angle greater than or equal to entry_3
    angle_data = hw_data[hw_data["H/W"] == closest_h_w].sort_values(by="ANGLE")
    valid_angles = angle_data[angle_data["ANGLE"] >= entry_3]
    if valid_angles.empty:
        closest_angle_row = angle_data.iloc[-1]  # Use the largest Angle if none match
    else:
        closest_angle_row = valid_angles.iloc[0]  # Use the smallest Angle greater than or equal to entry_3

    # Retrieve the base loss coefficient
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
