import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A9B2_outputs(stored_values, *_):
    """
    Calculates the outputs for case A9B2 using the stored input values.

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs.
    """
    # Extract required entries
    entry_1 = stored_values.get("entry_1")  # H (Height)
    entry_2 = stored_values.get("entry_2")  # W (Width)
    entry_3 = stored_values.get("entry_3")  # H₁ (Height 1)
    entry_4 = stored_values.get("entry_4")  # W₁ (Width 1)
    entry_5 = stored_values.get("entry_5")  # L (Length)
    entry_6 = stored_values.get("entry_6")  # Angle (degrees)
    entry_7 = stored_values.get("entry_7")  # Flow Rate (CFM)

    # Validate inputs
    if not all([entry_1, entry_2, entry_3, entry_4, entry_5, entry_6, entry_7]):
        return {f"Output {i+1}": None for i in range(4)}

    # Get the relevant data for A9B2
    df = get_case_table("A9B2")

    # Calculate hydraulic diameter for upstream (D) and downstream (D₁)
    hydraulic_diameter = 2 * (entry_1 * entry_2) / (entry_1 + entry_2)  # Upstream
    hydraulic_diameter_1 = 2 * (entry_3 * entry_4) / (entry_3 + entry_4)  # Downstream

    # Calculate velocity using downstream dimensions (H₁ and W₁)
    area_1 = (entry_3 * entry_4) / 144  # Area 1 in square feet
    velocity = entry_7 / area_1  # Velocity in ft/min

    # Calculate L/D
    length_diameter_ratio = entry_5 / hydraulic_diameter

    # Loss coefficient calculation
    if "L/D" not in df.columns or "ANGLE" not in df.columns or "C" not in df.columns or "A/A1" not in df.columns:
        raise KeyError("Data for A9B2 must include 'L/D', 'ANGLE', 'C', and 'A/A1' columns.")

    # Match L/D
    ld_data = df[["L/D", "ANGLE", "C"]].dropna().sort_values(by="L/D")
    valid_ld = ld_data[ld_data["L/D"] <= length_diameter_ratio]
    if valid_ld.empty:
        closest_ld_row = ld_data.iloc[0]  # Use the smallest L/D if none match
    else:
        closest_ld_row = valid_ld.iloc[-1]  # Use the largest L/D less than or equal to length_diameter_ratio

    # Match Angle within the closest L/D group
    closest_ld_value = closest_ld_row["L/D"]
    angle_data = ld_data[ld_data["L/D"] == closest_ld_value].sort_values(by="ANGLE")
    valid_angle = angle_data[angle_data["ANGLE"] <= entry_6] if entry_6 < 60 else angle_data[angle_data["ANGLE"] >= entry_6]
    if valid_angle.empty:
        closest_angle_row = angle_data.iloc[0] if entry_6 < 60 else angle_data.iloc[-1]  # Round down or up based on angle
    else:
        closest_angle_row = valid_angle.iloc[0] if entry_6 < 60 else valid_angle.iloc[-1]

    # Retrieve the base loss coefficient
    loss_coefficient_base = closest_angle_row["C"]

    # Correction factor using area ratio (A/A1)
    area = (entry_1 * entry_2) / 144  # Area in square feet
    area_ratio = area / area_1
    correction_data = df[["A/A1", "C"]].dropna().sort_values(by="A/A1")
    valid_correction = correction_data[correction_data["A/A1"] <= area_ratio]
    if valid_correction.empty:
        correction_row = correction_data.iloc[0]  # Use the smallest A/A1 if none match
    else:
        correction_row = valid_correction.iloc[-1]  # Use the largest A/A1 less than or equal to area_ratio

    correction_factor = correction_row["C"]

    # Final corrected loss coefficient
    corrected_loss_coefficient = loss_coefficient_base * correction_factor

    # Final calculations
    velocity_pressure = (velocity / 4005) ** 2
    pressure_loss = corrected_loss_coefficient * velocity_pressure

    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": corrected_loss_coefficient,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }
