import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A11B_outputs(inputs, data):
    """
    Calculate outputs for A11B case (diverging junction with conical tee).

    Inputs:
        inputs: dict with keys:
            entry_1: Main Diameter (in)
            entry_2: Branch Diameter (in)
            entry_3: Converged Flow Rate (cfm)
            entry_4: Branch Flow Rate (cfm)
        data: Pandas DataFrame containing the lookup table.

    Returns:
        dict: Output values for branch and main.
    """
    try:
        D_main = inputs.get("entry_1")
        D_branch = inputs.get("entry_2")
        Qc = inputs.get("entry_3")  # Converged flow
        Qb = inputs.get("entry_4")  # Branch flow

        if None in [D_main, D_branch, Qc, Qb]:
            return {"Error": "Missing input values."}

        # Area calculations
        A_main = math.pi * (D_main / 12 / 2) ** 2
        A_branch = math.pi * (D_branch / 12 / 2) ** 2

        # Velocity calculations
        Vc = Qc / A_main
        Vs = (Qc - Qb) / A_main
        Vb = Qb / A_branch

        # Velocity pressures
        Pvb = (Vb / 4005) ** 2
        Pvs = (Vs / 4005) ** 2
        Pvc = (Vc / 4005) ** 2

        # Lookup branch loss coefficient
        branch_data = data.loc["A11B"]
        branch_data = branch_data[branch_data["PATH"] == "branch"]

        Vb_Vc = Vb / Vc
        branch_data["Vb/Vc Diff"] = abs(branch_data["Vb/Vc"] - Vb_Vc)
        branch_row = branch_data.sort_values("Vb/Vc Diff").iloc[0]
        C_branch = branch_row["C"]
        branch_loss = C_branch * Pvb

        # Lookup main loss coefficient
        main_data = data.loc["A11A"]
        main_data = main_data[(main_data["PATH"] == "main") & (main_data["NAME"] == "Tee or Wye, Main")]

        Vs_Vc = Vs / Vc
        main_data["Vs/Vc Diff"] = abs(main_data["Vs/Vc"] - Vs_Vc)
        main_row = main_data.sort_values("Vs/Vc Diff").iloc[0]
        C_main = main_row["C"]
        main_loss = C_main * Pvs

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

A11B_outputs.output_type = "branch_main"
