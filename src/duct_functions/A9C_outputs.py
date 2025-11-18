import math
import pandas as pd
import numpy as np

def A9C_outputs(stored_values, data):
    """
    Calculates the outputs for case A9C using the stored input values.

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs.
    """
    # Extract required entries
    entry_1 = stored_values.get("entry_1")  # D (Diameter of round section)
    entry_2 = stored_values.get("entry_2")  # H₁ (Height of rectangular section)
    entry_3 = stored_values.get("entry_3")  # W₁ (Width of rectangular section)
    entry_4 = stored_values.get("entry_4")  # Flow Rate (CFM)

    # Validate inputs
    if not all([entry_1, entry_2, entry_3, entry_4]):
        return {f"Output {i+1}": None for i in range(5)}

    # Ensure `data` contains the necessary index
    if "A9C" not in data.index:
        raise KeyError("Data must include 'A9C' index for calculations.")
    df = data.loc["A9C"]

    # Calculate cross-sectional areas
    area_round = math.pi * (entry_1 / 2) ** 2 / 144  # Area of round section in square feet
    area_rect = (entry_2 * entry_3) / 144  # Area of rectangular section in square feet

    # Check for area mismatch (flag condition)
    area_flag = "Area of round section exceeds area of rectangular section" if area_round > area_rect else None

    # Calculate velocity using rectangular section (H₁ and W₁)
    velocity = entry_4 / area_rect  # Velocity in ft/min

    # Calculate Reynolds number
    reynolds_number = 8.56 * entry_1 * velocity

    # Loss coefficient calculation
    if "Re" not in df.columns or "C" not in df.columns:
        raise KeyError("Data for A9C must include 'Re' and 'C' columns.")

    # Match Reynolds number to find the closest value in the 'Re' column
    re_data = df[["Re", "C"]].dropna().sort_values(by="Re")
    valid_re = re_data[re_data["Re"] <= reynolds_number]
    if valid_re.empty:
        closest_re_row = re_data.iloc[0]  # Use the smallest Re if none match
    else:
        closest_re_row = valid_re.iloc[-1]  # Use the largest Re less than or equal to reynolds_number

    # Retrieve the loss coefficient
    loss_coefficient = closest_re_row["C"]

    # Final calculations
    velocity_pressure = (velocity / 4005) ** 2
    pressure_loss = loss_coefficient * velocity_pressure

    # Return outputs
    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
        "Flag": area_flag,  # None if no mismatch
    }
