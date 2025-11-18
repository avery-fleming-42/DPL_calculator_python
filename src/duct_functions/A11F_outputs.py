import math
import pandas as pd
import numpy as np

def A11F_outputs(inputs, data):
    """
    Calculate outputs for A11F case.

    Inputs:
        inputs: dict with keys:
            entry_1: Main Diameter (in)
            entry_2: Branch Diameter (in)
            entry_3: Main Upstream Flow Rate (cfm)
            entry_4: Branch Flow Rate (cfm)
        data: Pandas DataFrame containing the lookup table.

    Returns:
        dict: Output values for branch and main.
    """
    try:
        D_main = inputs.get("entry_1")
        D_branch = inputs.get("entry_2")
        Qc = inputs.get("entry_3")  # Converged (upstream) flow
        Qb = inputs.get("entry_4")  # Branch flow

        if None in [D_main, D_branch, Qc, Qb]:
            return {"Error": "Missing input values."}

        A_main = math.pi * (D_main / 12 / 2) ** 2
        A_branch = math.pi * (D_branch / 12 / 2) ** 2

        Vc = Qc / A_main
        Vs = (Qc - Qb) / A_main
        Vb = Qb / A_branch

        Pvb = (Vb / 4005) ** 2
        Pvs = (Vs / 4005) ** 2
        Pvc = (Vc / 4005) ** 2

        # --- Branch Loss Coefficient ---
        try:
            df_branch = data.loc["A11F"]
            branch_data = df_branch[df_branch["PATH"] == "branch"]
        except KeyError:
            return {"Error": "A11F branch data not found in Excel."}

        Vb_Vc = Vb / Vc
        branch_data["Vb/Vc Diff"] = abs(branch_data["Vb/Vc"] - Vb_Vc)
        branch_row = branch_data.sort_values("Vb/Vc Diff").iloc[0]
        C_branch = branch_row["C"]
        branch_loss = C_branch * Pvb

        # --- Main Loss Coefficient (fallback to A11A main data) ---
        try:
            df_main = data.loc["A11A"]
            main_data = df_main[(df_main["PATH"] == "main") & (df_main["NAME"] == "Tee or Wye, Main")]
        except KeyError:
            return {"Error": "A11A main data not found in Excel."}

        Vs_Vc = Vs / Vc
        main_data["Vs/Vc Diff"] = abs(main_data["Vs/Vc"] - Vs_Vc)
        main_row = main_data.sort_values("Vs/Vc Diff").iloc[0]
        C_main = main_row["C"]
        main_loss = C_main * Pvs

        return {
            # Branch Outputs
            "Branch Velocity (ft/min)": Vb,
            "Branch Velocity Pressure (in w.c.)": Pvb,
            "Branch Loss Coefficient": C_branch,
            "Branch Pressure Loss (in w.c.)": branch_loss,
            # Main Outputs
            "Main, Source Velocity (ft/min)": Vs,
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Source Velocity Pressure (in w.c.)": Pvs,
            "Main, Converged Velocity Pressure (in w.c.)": Pvc,
            "Main Loss Coefficient": C_main,
            "Main Pressure Loss (in w.c.)": main_loss,
        }

    except Exception as e:
        return {"Error": str(e)}

A11F_outputs.output_type = "branch_main"
