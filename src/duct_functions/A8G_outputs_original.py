import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A8G_outputs(stored_values, *_):
    """
    Calculates the outputs for case A8G using the stored input values.

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs.
    """
    # Extract required entries
    entry_1 = stored_values.get("entry_1")  # H (Height)
    entry_2 = stored_values.get("entry_2")  # H₁ (Height 1)
    entry_3 = stored_values.get("entry_3")  # W (Width)
    entry_4 = stored_values.get("entry_4")  # Angle (degrees)
    entry_5 = stored_values.get("entry_5")  # Flow Rate (CFM)

    # Validate inputs
    if not all([entry_1, entry_2, entry_3, entry_4, entry_5]):
        return {f"Output {i+1}": None for i in range(4)}

    # Get the relevant data for A8G
    df = get_case_table("A8G")

    # Calculate velocity
    area = (entry_1 * entry_3) / 144  # Area in square feet
    velocity = entry_5 / area  # Velocity in ft/min

    # Calculate area ratio (A1/A)
    area_1 = (entry_2 * entry_3) / 144  # Area 1 in square feet
    area_ratio = area_1 / area

    # Loss coefficient calculation
    if "ANGLE" not in df.columns or "A1/A" not in df.columns or "C" not in df.columns:
        raise KeyError("Data for A8G must include 'ANGLE', 'A1/A', and 'C' columns.")

    # Match angle
    angle_data = df[["ANGLE", "A1/A", "C"]].dropna().sort_values(by="ANGLE")
    valid_angle = angle_data[angle_data["ANGLE"] >= entry_4]
    if valid_angle.empty:
        closest_angle_row = angle_data.iloc[-1]  # Use the largest ANGLE if none match
    else:
        closest_angle_row = valid_angle.iloc[0]  # Use the smallest ANGLE greater than or equal to entry_4

    # Match A1/A within the closest ANGLE group
    closest_angle_value = closest_angle_row["ANGLE"]
    area_data = angle_data[angle_data["ANGLE"] == closest_angle_value].sort_values(by="A1/A")
    valid_area = area_data[area_data["A1/A"] >= area_ratio]
    if valid_area.empty:
        closest_area_row = area_data.iloc[-1]  # Use the largest A1/A if none match
    else:
        closest_area_row = valid_area.iloc[0]  # Use the smallest A1/A greater than or equal to area_ratio

    # Retrieve the base loss coefficient
    loss_coefficient_base = closest_area_row["C"]

    # Final calculations
    velocity_pressure = (velocity / 4005) ** 2
    pressure_loss = loss_coefficient_base * velocity_pressure

    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient_base,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }
