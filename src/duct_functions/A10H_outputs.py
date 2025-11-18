import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A10H_outputs(stored_values, data):
    """
    Calculates the outputs for case A10H (Converging Rectangular Wye).

    Parameters:
    - stored_values: Dictionary containing user inputs.
    - data: DataFrame containing lookup data.

    Returns:
    - Dictionary of calculated outputs.
    """
    try:
        # Extract inputs
        H = stored_values.get("entry_1")   # Height (in)
        Wb = stored_values.get("entry_2")  # Branch Width (in)
        Ws = stored_values.get("entry_3")  # Main, Source Width (in)
        Wc = stored_values.get("entry_4")  # Main, Converged Width (in)
        Qs = stored_values.get("entry_5")  # Source Flow Rate (cfm) -- swapped
        Qb = stored_values.get("entry_6")  # Branch Flow Rate (cfm) -- swapped

        if not all([H, Wb, Ws, Wc, Qs, Qb]):
            return {"Error": "Missing input values. Please enter all required values."}

        # Area calculations (convert to ft²)
        Ab = (H * Wb) / 144
        As = (H * Ws) / 144
        Ac = (H * Wc) / 144

        # Velocity calculations (ft/min)
        Vb = Qb / Ab
        Vs = Qs / As
        Vc = (Qs + Qb) / Ac

        # Velocity pressures (in. w.c.)
        Pv_b = (Vb / 4005) ** 2
        Pv_s = (Vs / 4005) ** 2
        Pv_c = (Vc / 4005) ** 2

        # Ratios
        Ab_As = Ab / As
        Ab_Ac = Ab / Ac
        As_Ac = As / Ac
        Qb_Qc = Qb / (Qs + Qb)
        Qb_Qs = Qb / Qs if Qs > 0 else 0

        # --- Branch Data Lookup ---
        try:
            branch_data = data.loc["A10H"]
            branch_data = branch_data[branch_data["PATH"] == "branch"]
        except KeyError:
            return {"Error": "A10H branch data not found in Excel."}

        match_branch = branch_data[
            (branch_data["Ab/As"] >= Ab_As) &
            (branch_data["Ab/Ac"] >= Ab_Ac) &
            (branch_data["Qb/Qc"] >= Qb_Qc)
        ]
        branch_loss_coefficient = match_branch.iloc[0]["C"] if not match_branch.empty else None

        # --- Main Data Lookup ---
        try:
            main_data = data.loc["A10H"]
            main_data = main_data[main_data["PATH"] == "main"]
        except KeyError:
            return {"Error": "A10H main data not found in Excel."}

        match_main = main_data[
            (main_data["As/Ac"] >= As_Ac) &
            (main_data["Ab/Ac"] >= Ab_Ac) &
            (main_data["Qb/Qc"] <= Qb_Qc)
        ]
        main_loss_coefficient = match_main.iloc[0]["C"] if not match_main.empty else None

        # --- Pressure Losses ---
        branch_pressure_loss = branch_loss_coefficient * Pv_b if branch_loss_coefficient else None
        main_pressure_loss = main_loss_coefficient * Pv_s if main_loss_coefficient else None

        # --- Build Outputs Dictionary ---
        outputs = {}

        outputs.update({
            # Branch outputs
            "Branch Velocity (ft/min)": Vb,
            "Branch Velocity Pressure (in w.c.)": Pv_b,
            "Branch Loss Coefficient": branch_loss_coefficient,
            "Branch Pressure Loss (in w.c.)": branch_pressure_loss,
        })

        outputs.update({
            # Main outputs
            "Main, Source Velocity (ft/min)": Vs,
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Source Velocity Pressure (in w.c.)": Pv_s,
            "Main, Converged Velocity Pressure (in w.c.)": Pv_c,
            "Main Loss Coefficient": main_loss_coefficient,
            "Main Pressure Loss (in w.c.)": main_pressure_loss,
        })

        return outputs

    except Exception as e:
        return {"Error": str(e)}

# Specify case type
A10H_outputs.output_type = "branch_main"
print("[DEBUG] A10H_outputs module loaded, output_type =", A10H_outputs.output_type)
