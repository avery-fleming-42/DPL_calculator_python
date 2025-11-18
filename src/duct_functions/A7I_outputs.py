import math
import pandas as pd
import numpy as np

def A7I_outputs(stored_values, data):
    """
    Calculates the outputs for case A7I using the stored input values, including
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
    entry_3 = stored_values.get("entry_3")  # L (Length)
    entry_4 = stored_values.get("entry_4")  # Flow Rate (CFM)

    # Validate inputs
    if not all([entry_1, entry_2, entry_3, entry_4]):
        return {f"Output {i+1}": None for i in range(4)}

    # Ensure `data` contains the necessary index
    if "A7I" not in data.index:
        raise KeyError("Data must include 'A7I' index for calculations.")
    df = data.loc["A7I"]

    # Calculate velocity
    area = (entry_1 * entry_2) / 144  # Area in square feet
    velocity = entry_4 / area  # Velocity in ft/min

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

    # Calculate L/H and W/H ratios
    l_h_ratio = entry_3 / entry_1
    w_h_ratio = entry_2 / entry_1

    # Loss coefficient calculation
    if "L/H" not in df.columns or "C" not in df.columns or "W/H" not in df.columns:
        raise KeyError("Data for A7I must include 'L/H', 'C', and 'W/H' columns.")

    # Match L/H ratio
    lh_data = df[["L/H", "C"]].dropna().sort_values(by="L/H")
    if l_h_ratio <= 2:
        valid_lh = lh_data[lh_data["L/H"] <= l_h_ratio]
        if valid_lh.empty:
            closest_lh_row = lh_data.iloc[0]  # Use the smallest L/H if none match
        else:
            closest_lh_row = valid_lh.iloc[-1]  # Use the largest L/H less than or equal to l_h_ratio
    else:
        valid_lh = lh_data[lh_data["L/H"] >= l_h_ratio]
        if valid_lh.empty:
            closest_lh_row = lh_data.iloc[-1]  # Use the largest L/H if none match
        else:
            closest_lh_row = valid_lh.iloc[0]  # Use the smallest L/H greater than or equal to l_h_ratio

    # Retrieve the base loss coefficient
    loss_coefficient_base = closest_lh_row["C"]

    # Match W/H ratio for additional correction factor
    wh_data = df[["W/H", "C"]].dropna().sort_values(by="W/H")
    valid_wh = wh_data[wh_data["W/H"] <= w_h_ratio]
    if valid_wh.empty:
        closest_wh_row = wh_data.iloc[0]  # Use the smallest W/H if none match
    else:
        closest_wh_row = valid_wh.iloc[-1]  # Use the largest W/H less than or equal to w_h_ratio

    # Retrieve the correction factor from W/H
    wh_correction_factor = closest_wh_row["C"]

    # Final calculations
    loss_coefficient = loss_coefficient_base * wh_correction_factor * rnc_factor
    velocity_pressure = (velocity / 4005) ** 2
    pressure_loss = loss_coefficient * velocity_pressure

    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }
