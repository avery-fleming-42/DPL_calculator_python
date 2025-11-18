import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A8A_outputs(stored_values, *_):
    """
    Calculates the outputs for case A8A using the stored input values, including
    Reynolds number and loss coefficient.

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs.
    """
    # Extract required entries
    entry_1 = stored_values.get("entry_1")  # D (Diameter)
    entry_2 = stored_values.get("entry_2")  # D₁ (Diameter 1)
    entry_3 = stored_values.get("entry_3")  # Angle (degrees)
    entry_4 = stored_values.get("entry_4")  # Flow Rate (CFM)

    # Validate inputs
    if not all([entry_1, entry_2, entry_3, entry_4]):
        return {f"Output {i+1}": None for i in range(4)}

    # Get the relevant data for A8A
    df = get_case_table("A8A")

    # Calculate velocity
    area = math.pi * (entry_1 / 2) ** 2 / 144  # Area in square feet
    velocity = entry_4 / area  # Velocity in ft/min

    # Calculate Reynolds number
    reynolds_number = 8.56 * entry_1 * velocity

    # Calculate area ratio (A1/A)
    area_1 = math.pi * (entry_2 / 2) ** 2 / 144  # Area 1 in square feet
    area_ratio = area_1 / area

    # Loss coefficient calculation
    if "Re" not in df.columns or "A1/A" not in df.columns or "ANGLE" not in df.columns or "C" not in df.columns:
        raise KeyError("Data for A8A must include 'Re', 'A1/A', 'ANGLE', and 'C' columns.")

    # Match Reynolds number
    re_data = df[["Re", "A1/A", "ANGLE", "C"]].dropna().sort_values(by="Re")
    valid_re = re_data[re_data["Re"] <= reynolds_number]
    if valid_re.empty:
        closest_re_row = re_data.iloc[0]  # Use the smallest Re if none match
    else:
        closest_re_row = valid_re.iloc[-1]  # Use the largest Re less than or equal to reynolds_number

    # Match A1/A within the closest Re group
    closest_re_value = closest_re_row["Re"]
    area_data = re_data[re_data["Re"] == closest_re_value].sort_values(by="A1/A")
    valid_area = area_data[area_data["A1/A"] >= area_ratio]
    if valid_area.empty:
        closest_area_row = area_data.iloc[-1]  # Use the largest A1/A if none match
    else:
        closest_area_row = valid_area.iloc[0]  # Use the smallest A1/A greater than or equal to area_ratio

    # Match angle within the closest A1/A group
    closest_area_value = closest_area_row["A1/A"]
    angle_data = area_data[area_data["A1/A"] == closest_area_value].sort_values(by="ANGLE")
    if entry_3 < 90:
        valid_angle = angle_data[angle_data["ANGLE"] >= entry_3]
        if valid_angle.empty:
            closest_angle_row = angle_data.iloc[-1]  # Use the largest ANGLE if none match
        else:
            closest_angle_row = valid_angle.iloc[0]  # Use the smallest ANGLE greater than or equal to entry_3
    else:
        valid_angle = angle_data[angle_data["ANGLE"] <= entry_3]
        if valid_angle.empty:
            closest_angle_row = angle_data.iloc[0]  # Use the smallest ANGLE if none match
        else:
            closest_angle_row = valid_angle.iloc[-1]  # Use the largest ANGLE less than or equal to entry_3

    # Retrieve the base loss coefficient
    loss_coefficient_base = closest_angle_row["C"]

    # Final calculations
    velocity_pressure = (velocity / 4005) ** 2
    pressure_loss = loss_coefficient_base * velocity_pressure

    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient_base,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }
