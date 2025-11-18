import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A11K_outputs(stored_values, *_):
    """
    Calculate outputs for A11K case.

    Inputs:
        stored_values: dict with keys:
            entry_1: Main Diameter (in)
            entry_2: Branch Diameter (in)
            entry_3: Main Upstream / Converged Flow Rate (Qc, cfm)
            entry_4: Branch Flow Rate (Qb, cfm)

    Returns:
        dict: Output values for branch and main.
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        D_main = stored_values.get("entry_1")
        D_branch = stored_values.get("entry_2")
        Qc = stored_values.get("entry_3")  # Converged flow
        Qb = stored_values.get("entry_4")  # Branch flow

        if None in [D_main, D_branch, Qc, Qb]:
            return {"Error": "Missing input values."}

        # ==========================
        #   GEOMETRY & FLOW
        # ==========================
        A_main = math.pi * (D_main / 12.0 / 2.0) ** 2
        A_branch = math.pi * (D_branch / 12.0 / 2.0) ** 2

        Vc = Qc / A_main
        Vs = (Qc - Qb) / A_main
        Vb = Qb / A_branch

        Pvb = (Vb / 4005.0) ** 2
        Pvs = (Vs / 4005.0) ** 2
        Pvc = (Vc / 4005.0) ** 2

        # ==========================
        #   BRANCH LOSS COEFFICIENT (A11K)
        # ==========================
        try:
            branch_data = get_case_table("A11K")
            branch_data = branch_data[branch_data["PATH"] == "branch"].copy()
        except KeyError:
            return {"Error": "A11K branch data not found."}

        if branch_data.empty:
            return {"Error": "No branch data found for A11K."}

        Vb_Vc = Vb / Vc
        branch_data["Vb/Vc Diff"] = (branch_data["Vb/Vc"] - Vb_Vc).abs()
        branch_row = branch_data.sort_values("Vb/Vc Diff").iloc[0]

        C_branch = branch_row["C"]
        branch_loss = C_branch * Pvb

        # ==========================
        #   MAIN LOSS COEFFICIENT (A11A main)
        # ==========================
        try:
            main_data = get_case_table("A11A")
            main_data = main_data[
                (main_data["PATH"] == "main") &
                (main_data["NAME"] == "Tee or Wye, Main")
            ].copy()
        except KeyError:
            return {"Error": "A11A main data not found."}

        if main_data.empty:
            return {"Error": "No main data found for A11A (Tee or Wye, Main)."}

        Vs_Vc = Vs / Vc
        main_data["Vs/Vc Diff"] = (main_data["Vs/Vc"] - Vs_Vc).abs()
        main_row = main_data.sort_values("Vs/Vc Diff").iloc[0]

        C_main = main_row["C"]
        main_loss = C_main * Pvs

        # ==========================
        #   OUTPUTS
        # ==========================
        return {
            # Branch
            "Branch Velocity (ft/min)": Vb,
            "Branch Velocity Pressure (in w.c.)": Pvb,
            "Branch Loss Coefficient": C_branch,
            "Branch Pressure Loss (in w.c.)": branch_loss,
            # Main
            "Main, Source Velocity (ft/min)": Vs,
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Source Velocity Pressure (in w.c.)": Pvs,
            "Main, Converged Velocity Pressure (in w.c.)": Pvc,
            "Main Loss Coefficient": C_main,
            "Main Pressure Loss (in w.c.)": main_loss,
        }

    except Exception as e:
        return {"Error": str(e)}


A11K_outputs.output_type = "branch_main"
