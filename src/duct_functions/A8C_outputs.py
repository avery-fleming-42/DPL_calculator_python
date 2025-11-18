import math
import pandas as pd
import numpy as np

def A8C_outputs(stored_values, data):
    """
    Calculates the outputs for case A8C (Round to Rectangular Expansion).
    """
    entry_1 = stored_values.get("entry_1")  # H (in)
    entry_2 = stored_values.get("entry_2")  # W (in)
    entry_3 = stored_values.get("entry_3")  # D (in)
    entry_4 = stored_values.get("entry_4")  # L (in)
    entry_5 = stored_values.get("entry_5")  # Flow rate (cfm)

    if not all([entry_1, entry_2, entry_3, entry_4, entry_5]):
        return {f"Output {i+1}": None for i in range(4)}

    if "A8B" not in data.index:
        raise KeyError("Data must include 'A8B' index for calculations.")

    df = data.loc["A8B"]

    # Areas
    area_round = math.pi * (entry_3 / 2) ** 2 / 144  # ft²
    area_rect = (entry_1 * entry_2) / 144  # ft²

    # Velocity (ft/min) based on original (round) area
    velocity = entry_5 / area_round

    # Calculate angle (degrees)
    try:
        tan_half_theta = (1.13 * math.sqrt(entry_1 * entry_2) - entry_3) / (2 * entry_4)
        theta_deg = math.degrees(2 * math.atan(tan_half_theta))
    except (ZeroDivisionError, ValueError) as e:
        print(f"[ERROR] Invalid angle calculation: {e}")
        return {f"Output {i+1}": None for i in range(4)}

    # Area ratio
    area_ratio = area_rect / area_round

    if "ANGLE" not in df.columns or "A1/A" not in df.columns or "C" not in df.columns:
        raise KeyError("A8B data must include 'ANGLE', 'A1/A', and 'C' columns.")

    # Lookup closest ANGLE
    angle_data = df[["ANGLE", "A1/A", "C"]].dropna().sort_values(by="ANGLE")
    valid_angle = angle_data[angle_data["ANGLE"] >= theta_deg]
    if valid_angle.empty:
        closest_angle_row = angle_data.iloc[-1]
    else:
        closest_angle_row = valid_angle.iloc[0]

    closest_angle = closest_angle_row["ANGLE"]

    # Lookup closest A1/A within the selected angle
    area_subset = angle_data[angle_data["ANGLE"] == closest_angle].sort_values(by="A1/A")
    valid_area = area_subset[area_subset["A1/A"] >= area_ratio]
    if valid_area.empty:
        closest_area_row = area_subset.iloc[-1]
    else:
        closest_area_row = valid_area.iloc[0]

    loss_coefficient = closest_area_row["C"]

    velocity_pressure = (velocity / 4005) ** 2
    pressure_loss = loss_coefficient * velocity_pressure

    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }
