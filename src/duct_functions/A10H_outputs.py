import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A10H_outputs(stored_values, *_):
    """
    Calculates the outputs for case A10H (Converging Rectangular Wye).

    Parameters:
    - stored_values: Dictionary containing user inputs.

    Returns:
    - Dictionary of calculated outputs.
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        H = stored_values.get("entry_1")   # Height (in)
        Wb = stored_values.get("entry_2")  # Branch Width (in)
        Ws = stored_values.get("entry_3")  # Main, Source Width (in)
        Wc = stored_values.get("entry_4")  # Main, Converged Width (in)
        Qs = stored_values.get("entry_5")  # Source Flow Rate (cfm)
        Qb = stored_values.get("entry_6")  # Branch Flow Rate (cfm)

        if not all([H, Wb, Ws, Wc, Qs, Qb]):
            return {
                "Error": "Missing input values. Please enter all required values."
            }

        # ==========================
        #   GEOMETRY & FLOW
        # ==========================
        # Areas (ft²)
        Ab = (H * Wb) / 144.0
        As = (H * Ws) / 144.0
        Ac = (H * Wc) / 144.0

        # Velocities (ft/min)
        Vb = Qb / Ab
        Vs = Qs / As
        Vc = (Qs + Qb) / Ac

        # Velocity pressures (in. w.c.)
        Pv_b = (Vb / 4005.0) ** 2
        Pv_s = (Vs / 4005.0) ** 2
        Pv_c = (Vc / 4005.0) ** 2

        # Ratios
        Ab_As = Ab / As
        Ab_Ac = Ab / Ac
        As_Ac = As / Ac
        Qb_Qc = Qb / (Qs + Qb)
        Qb_Qs = Qb / Qs if Qs > 0 else 0  # kept for completeness / future checks

        # ==========================
        #   BRANCH DATA LOOKUP
        # ==========================
        branch_data = get_case_table("A10H")
        branch_data = branch_data[branch_data["PATH"] == "branch"].copy()

        if branch_data.empty:
            return {"Error": "No branch data found for A10H."}

        match_branch = branch_data[
            (branch_data["Ab/As"] >= Ab_As) &
            (branch_data["Ab/Ac"] >= Ab_Ac) &
            (branch_data["Qb/Qc"] >= Qb_Qc)
        ]

        if not match_branch.empty:
            branch_loss_coefficient = match_branch.iloc[0]["C"]
        else:
            # Fallback: use last row if no inequality match
            branch_loss_coefficient = branch_data.iloc[-1]["C"]

        # ==========================
        #   MAIN DATA LOOKUP
        # ==========================
        main_data = get_case_table("A10H")
        main_data = main_data[main_data["PATH"] == "main"].copy()

        if main_data.empty:
            return {"Error": "No main data found for A10H."}

        match_main = main_data[
            (main_data["As/Ac"] >= As_Ac) &
            (main_data["Ab/Ac"] >= Ab_Ac) &
            (main_data["Qb/Qc"] <= Qb_Qc)
        ]

        if not match_main.empty:
            main_loss_coefficient = match_main.iloc[0]["C"]
        else:
            # Fallback: use first row if no inequality match
            main_loss_coefficient = main_data.iloc[0]["C"]

        # ==========================
        #   PRESSURE LOSSES
        # ==========================
        branch_pressure_loss = branch_loss_coefficient * Pv_b
        main_pressure_loss = main_loss_coefficient * Pv_s

        # ==========================
        #   OUTPUTS
        # ==========================
        outputs = {}

        # Branch outputs
        outputs.update({
            "Branch Velocity (ft/min)": Vb,
            "Branch Velocity Pressure (in w.c.)": Pv_b,
            "Branch Loss Coefficient": branch_loss_coefficient,
            "Branch Pressure Loss (in w.c.)": branch_pressure_loss,
        })

        # Main outputs
        outputs.update({
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
