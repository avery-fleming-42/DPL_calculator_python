import math
import pandas as pd
import numpy as np

def A10B_outputs(stored_values, data):
    """
    Calculates outputs for case A10B, handling both branch and main paths.

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., D_main, D_branch, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary containing flat outputs for branch and main.
    """
    # Extract required entries
    D_main = stored_values.get("entry_1")  # Diameter of the main
    D_branch = stored_values.get("entry_2")  # Diameter of the branch
    Q_source = stored_values.get("entry_3")  # Flow rate in the main
    Q_branch = stored_values.get("entry_4")  # Flow rate in the branch

    # Validate inputs
    if not all([D_main, D_branch, Q_source, Q_branch]):
        return {f"Output {i+1}": None for i in range(10)}

    # Calculate velocities
    area_main = math.pi * (D_main / 2) ** 2 / 144  # Area of the main in square feet
    area_branch = math.pi * (D_branch / 2) ** 2 / 144  # Area of the branch in square feet
    Q_converged = Q_source + Q_branch  # Total flow rate after convergence

    velocity_branch = Q_branch / area_branch  # Velocity in the branch
    velocity_source = Q_source / area_main  # Velocity in the main (source)
    velocity_converged = Q_converged / area_main  # Velocity after convergence

    # Filter data for branch
    branch_data = data[(data.index == "A10B") & (data["PATH"] == "branch")]

    # Calculate branch loss coefficient
    # Match Qb/Qc
    Qb_Qc = Q_branch / Q_converged
    branch_q_data = branch_data[["Qb/Qc", "Ab/Ac", "C"]].dropna().sort_values(by="Qb/Qc")
    valid_branch_q = branch_q_data[branch_q_data["Qb/Qc"] >= Qb_Qc]
    closest_branch_q = valid_branch_q.iloc[0] if not valid_branch_q.empty else branch_q_data.iloc[-1]

    # Match Ab/Ac
    Ab_Ac = area_branch / area_main
    branch_a_data = branch_data[["Ab/Ac", "C"]].dropna().sort_values(by="Ab/Ac")
    valid_branch_a = branch_a_data[branch_a_data["Ab/Ac"] <= Ab_Ac]
    closest_branch_a = valid_branch_a.iloc[-1] if not valid_branch_a.empty else branch_a_data.iloc[0]

    # Final branch loss coefficient
    branch_loss_coefficient = closest_branch_q["C"] * closest_branch_a["C"]

    # Branch pressure loss
    branch_velocity_pressure = (velocity_branch / 4005) ** 2
    branch_pressure_loss = branch_loss_coefficient * branch_velocity_pressure

    # Filter data for main
    main_data = data[(data.index == "A10B") & (data["PATH"] == "main")]

    # Calculate main loss coefficient
    # Match Qb/Qc
    Qb_Qc_main = Q_branch / Q_converged
    main_q_data = main_data[["Qb/Qc", "C"]].dropna().sort_values(by="Qb/Qc")
    valid_main_q = main_q_data[main_q_data["Qb/Qc"] >= Qb_Qc_main]
    closest_main_q = valid_main_q.iloc[0] if not valid_main_q.empty else main_q_data.iloc[-1]

    # Final main loss coefficient
    main_loss_coefficient = closest_main_q["C"]

    # Main pressure loss
    source_velocity_pressure = (velocity_source / 4005) ** 2
    converged_velocity_pressure = (velocity_converged / 4005) ** 2
    main_pressure_loss = main_loss_coefficient * source_velocity_pressure

    # --- Return flat dictionary ---
    outputs = {}

    # Branch outputs
    outputs.update({
        "Branch Velocity (ft/min)": velocity_branch,
        "Branch Velocity Pressure (in w.c.)": branch_velocity_pressure,
        "Branch Loss Coefficient": branch_loss_coefficient,
        "Branch Pressure Loss (in w.c.)": branch_pressure_loss,
    })

    # Main outputs
    outputs.update({
        "Main, Source Velocity (ft/min)": velocity_source,
        "Main, Converged Velocity (ft/min)": velocity_converged,
        "Main, Source Velocity Pressure (in w.c.)": source_velocity_pressure,
        "Main, Converged Velocity Pressure (in w.c.)": converged_velocity_pressure,
        "Main Loss Coefficient": main_loss_coefficient,
        "Main Pressure Loss (in w.c.)": main_pressure_loss,
    })

    return outputs

A10B_outputs.output_type = "branch_main"
