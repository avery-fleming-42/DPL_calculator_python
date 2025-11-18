import math
import pandas as pd
import numpy as np
import sys
def A10A1_outputs(stored_values, data):
    """
    Calculates the outputs for case A10A1 (converging junctions) for both branch and main.

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs for both branch and main.
    """
    # Extract required entries
    entry_1 = stored_values.get("entry_1")  # D main (Diameter of main duct)
    entry_2 = stored_values.get("entry_2")  # D branch (Diameter of branch duct)
    entry_3 = stored_values.get("entry_3")  # Q source (Flow rate from main duct)
    entry_4 = stored_values.get("entry_4")  # Q branch (Flow rate from branch duct)

    # Validate inputs
    if not all([entry_1, entry_2, entry_3, entry_4]):
        return {f"Output {i+1}": None for i in range(10)}

    # Extract data for branch (ID = "A10A1") and main (ID = "A10A2")
    branch_data = data.loc["A10A1"]
    main_data = data.loc["A10A2"]

    # Calculate cross-sectional areas
    area_main = math.pi * (entry_1 / 2) ** 2 / 144  # Main area in ft²
    area_branch = math.pi * (entry_2 / 2) ** 2 / 144  # Branch area in ft²

    # Calculate velocities
    velocity_branch = entry_4 / area_branch  # Branch velocity in ft/min
    velocity_source = entry_3 / area_main  # Source velocity in ft/min
    velocity_converged = (entry_3 + entry_4) / area_main  # Converged velocity in ft/min

    # Branch loss coefficient
    vb_vc_ratio = velocity_branch / velocity_converged
    ab_ac_ratio = area_branch / area_main

    vb_vc_data = branch_data[["Vb/Vc", "Ab/Ac", "C"]].dropna().sort_values(by=["Vb/Vc", "Ab/Ac"])
    valid_vb_vc = vb_vc_data[vb_vc_data["Vb/Vc"] >= vb_vc_ratio]
    if valid_vb_vc.empty:
        branch_vb_vc_row = vb_vc_data.iloc[-1]
    else:
        branch_vb_vc_row = valid_vb_vc.iloc[0]

    valid_ab_ac = vb_vc_data[vb_vc_data["Ab/Ac"] >= ab_ac_ratio]
    if valid_ab_ac.empty:
        branch_ab_ac_row = vb_vc_data.iloc[-1]
    else:
        branch_ab_ac_row = valid_ab_ac.iloc[0]

    branch_loss_coefficient = branch_ab_ac_row["C"]

    # Main loss coefficient
    vs_vc_ratio = velocity_source / velocity_converged

    vs_vc_data = main_data[["Vs/Vc", "Ab/Ac", "C"]].dropna().sort_values(by=["Vs/Vc", "Ab/Ac"])
    valid_vs_vc = vs_vc_data[vs_vc_data["Vs/Vc"] >= vs_vc_ratio]
    if valid_vs_vc.empty:
        main_vs_vc_row = vs_vc_data.iloc[-1]
    else:
        main_vs_vc_row = valid_vs_vc.iloc[0]

    valid_ab_ac_main = vs_vc_data[vs_vc_data["Ab/Ac"] >= ab_ac_ratio]
    if valid_ab_ac_main.empty:
        main_ab_ac_row = vs_vc_data.iloc[-1]
    else:
        main_ab_ac_row = valid_ab_ac_main.iloc[0]

    main_loss_coefficient = main_ab_ac_row["C"]

    # Calculate pressures
    velocity_pressure_branch = (velocity_branch / 4005) ** 2
    velocity_pressure_source = (velocity_source / 4005) ** 2
    velocity_pressure_converged = (velocity_converged / 4005) ** 2

    branch_pressure_loss = branch_loss_coefficient * velocity_pressure_branch
    main_pressure_loss = main_loss_coefficient * velocity_pressure_source

    # Return results
    return {
        # Branch outputs
        "Branch Velocity (ft/min)": velocity_branch,
        "Branch Velocity Pressure (in w.c.)": velocity_pressure_branch,
        "Branch Loss Coefficient": branch_loss_coefficient,
        "Branch Pressure Loss (in w.c.)": branch_pressure_loss,
        # Main outputs
        "Main, Source Velocity (ft/min)": velocity_source,
        "Main, Converged Velocity (ft/min)": velocity_converged,
        "Main, Source Velocity Pressure (in w.c.)": velocity_pressure_source,
        "Main, Converged Velocity Pressure (in w.c.)": velocity_pressure_converged,
        "Main Loss Coefficient": main_loss_coefficient,
        "Main Pressure Loss (in w.c.)": main_pressure_loss,
    }
A10A1_outputs.output_type = "branch_main"