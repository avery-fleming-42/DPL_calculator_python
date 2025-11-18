import math
import pandas as pd
import numpy as np

def A10F_outputs(stored_values, data):
    """
    Calculates the outputs for case A10F (converging junctions) for both branch and main.

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., entry_1, entry_2, etc.).
    - data: DataFrame containing relevant data for the calculations.

    Returns:
    - Dictionary of calculated outputs for both branch and main OR an error message if conditions are not met.
    """
    try:
        # Extract required entries
        entry_1 = stored_values.get("entry_1")  # Main Height (in)
        entry_2 = stored_values.get("entry_2")  # Main Width (in)
        entry_3 = stored_values.get("entry_3")  # Main Source Flow Rate (Qs, cfm)
        entry_4 = stored_values.get("entry_4")  # Branch Flow Rate (Qb, cfm)

        # Validate inputs
        if not all([entry_1, entry_2, entry_3, entry_4]):
            return {"Error": "Missing input values. Please enter all required values."}

        # Calculate cross-sectional areas (ft²)
        area_main = (entry_1 * entry_2) / 144  # Ac
        area_branch = area_main / 2            # Ab = Ac / 2

        # Calculate flow rates
        Q_source = entry_3
        Q_branch = entry_4
        Q_converged = Q_source + Q_branch

        # Calculate velocities (ft/min)
        velocity_source = Q_source / area_main
        velocity_converged = Q_converged / area_main
        velocity_branch = Q_branch / area_branch

        # Flow Rate Ratios
        qb_qc_ratio = Q_branch / Q_converged
        qb_qs_ratio = Q_branch / Q_source

        # --- ERROR CHECK: Qb/Qs must be >= 0.4 ---
        if qb_qs_ratio < 0.4:
            return {"Error": "Invalid Input: Qb/Qs must be at least 0.4. Increase branch flow rate (Qb) or decrease source flow rate (Qs)."}

        # --- Branch Loss Coefficient ---
        branch_data = data.loc["A10F"]
        branch_data = branch_data[branch_data["PATH"] == "branch"]

        valid_vc = branch_data[branch_data["Vc"] <= velocity_converged]
        branch_vc_row = valid_vc.iloc[-1] if not valid_vc.empty else branch_data.iloc[0]

        valid_qb_qc = branch_data[branch_data["Qb/Qc"] >= qb_qc_ratio]
        branch_qb_qc_row = valid_qb_qc.iloc[0] if not valid_qb_qc.empty else branch_data.iloc[-1]

        branch_loss_coefficient = branch_qb_qc_row["C"]

        # --- Main Loss Coefficient ---
        main_data = data.loc["A10M"]
        main_data = main_data[main_data["PATH"] == "main"]

        as_ac_ratio = 1.0
        ab_ac_ratio = 0.5

        main_data["As/Ac Diff"] = abs(main_data["As/Ac"] - as_ac_ratio)
        main_as_ac_row = main_data.loc[main_data["As/Ac Diff"].idxmin()]

        valid_ab_ac = main_data[main_data["Ab/Ac"] >= ab_ac_ratio]
        main_ab_ac_row = valid_ab_ac.iloc[0] if not valid_ab_ac.empty else main_data.iloc[-1]

        valid_qb_qs = main_data[main_data["Qb/Qs"] <= qb_qs_ratio]
        main_qb_qs_row = valid_qb_qs.iloc[-1] if not valid_qb_qs.empty else main_data.iloc[0]

        main_loss_coefficient = main_qb_qs_row["C"]

        # --- Velocity Pressures ---
        branch_velocity_pressure = (velocity_branch / 4005) ** 2
        source_velocity_pressure = (velocity_source / 4005) ** 2
        converged_velocity_pressure = (velocity_converged / 4005) ** 2

        # --- Pressure Losses ---
        branch_pressure_loss = branch_loss_coefficient * branch_velocity_pressure
        main_pressure_loss = main_loss_coefficient * source_velocity_pressure

        # --- Build Outputs Dictionary ---
        outputs = {}

        outputs.update({
            # Branch outputs
            "Branch Velocity (ft/min)": velocity_branch,
            "Branch Velocity Pressure (in w.c.)": branch_velocity_pressure,
            "Branch Loss Coefficient": branch_loss_coefficient,
            "Branch Pressure Loss (in w.c.)": branch_pressure_loss,
        })

        outputs.update({
            # Main outputs
            "Main, Source Velocity (ft/min)": velocity_source,
            "Main, Converged Velocity (ft/min)": velocity_converged,
            "Main, Source Velocity Pressure (in w.c.)": source_velocity_pressure,
            "Main, Converged Velocity Pressure (in w.c.)": converged_velocity_pressure,
            "Main Loss Coefficient": main_loss_coefficient,
            "Main Pressure Loss (in w.c.)": main_pressure_loss,
        })

        return outputs

    except Exception as e:
        return {"Error": str(e)}

# Specify case type
A10F_outputs.output_type = "branch_main"
print("[DEBUG] A10F_outputs module loaded, output_type =", A10F_outputs.output_type)
