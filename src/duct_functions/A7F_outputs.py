import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A7F_outputs(stored_values, *_):
    """
    Calculates the outputs for case A7F using the stored input values, including
    Reynolds Number Correction Factor (RNCF).

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs.
    """
    # Extract required entries
    entry_1 = stored_values.get("entry_1")  # H (Height)
    entry_2 = stored_values.get("entry_2")  # W (Width)
    entry_3 = stored_values.get("entry_3")  # R (Radius)
    entry_4 = stored_values.get("entry_4")  # θ (degrees)
    entry_5 = stored_values.get("entry_5")  # Flow Rate (CFM)

    # Validate inputs
    if not all([entry_1, entry_2, entry_3, entry_4, entry_5]):
        return {f"Output {i+1}": None for i in range(4)}

    # Get the relevant data for A7F
    df = get_case_table("A7F")

    # Calculate velocity
    area = (entry_1 * entry_2) / 144  # Area in square feet
    velocity = entry_5 / area  # Velocity in ft/min

    # Calculate hydraulic diameter
    hydraulic_diameter = 2 * (entry_1 * entry_2) / (entry_1 + entry_2)  # Hydraulic diameter in ft

    # Calculate Reynolds number and equivalent diameter
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

    # Calculate R/W and H/W ratios
    r_w_ratio = entry_3 / entry_2
    h_w_ratio = entry_1 / entry_2

    # Loss coefficient calculation
    if "R/W" not in df.columns or "H/W" not in df.columns or "C" not in df.columns:
        raise KeyError("Data for A7F must include 'R/W', 'H/W', and 'C' columns.")

    # Match R/W ratio
    rw_data = df[["R/W", "H/W", "C"]].dropna().sort_values(by=["R/W", "H/W"])
    valid_rw = rw_data[rw_data["R/W"] <= r_w_ratio]
    if valid_rw.empty:
        closest_rw_row = rw_data.iloc[0]  # Use the smallest R/W if none match
    else:
        closest_rw_row = valid_rw.iloc[-1]  # Use the largest R/W less than or equal to r_w_ratio

    closest_r_w = closest_rw_row["R/W"]

    # Match H/W ratio within the closest R/W group
    hw_data = rw_data[rw_data["R/W"] == closest_r_w].sort_values(by="H/W")
    if h_w_ratio <= 3:
        valid_hw = hw_data[hw_data["H/W"] <= h_w_ratio]
        if valid_hw.empty:
            closest_hw_row = hw_data.iloc[0]  # Use the smallest H/W if none match
        else:
            closest_hw_row = valid_hw.iloc[-1]  # Use the largest H/W less than or equal to h_w_ratio
    else:
        valid_hw = hw_data[hw_data["H/W"] >= h_w_ratio]
        if valid_hw.empty:
            closest_hw_row = hw_data.iloc[-1]  # Use the largest H/W if none match
        else:
            closest_hw_row = valid_hw.iloc[0]  # Use the smallest H/W greater than or equal to h_w_ratio

    # Retrieve the base loss coefficient
    loss_coefficient_base = closest_hw_row["C"]

    # Apply angle correction if angle is less than 90 degrees
    angle_correction_factors = {
        90: 1.00,
        75: 0.88,
        60: 0.75,
        45: 0.60,
        30: 0.45
    }
    applicable_angle = max([a for a in angle_correction_factors if entry_4 >= a], default=30)
    angle_correction = angle_correction_factors[applicable_angle]

    # Final calculations
    loss_coefficient = loss_coefficient_base * rnc_factor * angle_correction
    velocity_pressure = (velocity / 4005) ** 2
    pressure_loss = loss_coefficient * velocity_pressure

    # Return results as a dictionary
    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }
