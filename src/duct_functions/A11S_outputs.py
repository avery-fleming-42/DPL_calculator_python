import math
import pandas as pd
import numpy as np

def A11S_outputs(inputs, data):
    """
    Calculate outputs for A11S case (Round Branch to Rectangular Main).

    Inputs:
        inputs: dict with keys:
            entry_1: Main Height (in),
            entry_2: Main Width (in),
            entry_3: Branch Diameter (in),
            entry_4: Main Upstream Flow Rate (cfm),
            entry_5: Branch Flow Rate (cfm)
        data: Pandas DataFrame containing the lookup table.

    Returns:
        dict: Output values for branch and main.
    """
    try:
        # Extract inputs
        H_main = inputs.get("entry_1")  # Main height (in)
        W_main = inputs.get("entry_2")  # Main width (in)
        D_branch = inputs.get("entry_3")  # Branch diameter (in)
        Qc = inputs.get("entry_4")  # Main flow (cfm)
        Qb = inputs.get("entry_5")  # Branch flow (cfm)

        if None in [H_main, W_main, D_branch, Qc, Qb]:
            return {"Error": "Missing input values."}

        # --- Area Calculations ---
        A_main = (H_main * W_main) / 144  # ft²
        A_branch = (math.pi * (D_branch / 12) ** 2) / 4  # ft²

        # --- Velocity Calculations ---
        Vc = Qc / A_main
        Vb = Qb / A_branch
        Vs = (Qc - Qb) / A_main

        # --- Velocity Pressures ---
        Pvb = (Vb / 4005) ** 2
        Pvs = (Vs / 4005) ** 2
        Pvc = (Vc / 4005) ** 2

        # --- Ratios ---
        Vb_Vc = Vb / Vc
        Qb_Qc = Qb / Qc
        Vs_Vc = Vs / Vc

        # --- Branch Loss Coefficient Lookup ---
        try:
            df_branch = data.loc["A11S"]
            branch_data = df_branch[df_branch["PATH"] == "branch"].copy()
        except KeyError:
            return {"Error": "A11S branch data not found in Excel."}

        branch_data["Vb/Vc Diff"] = branch_data["Vb/Vc"].apply(lambda x: abs(x - Vb_Vc) if x >= Vb_Vc else float("inf"))
        branch_data["Qb/Qc Diff"] = branch_data["Qb/Qc"].apply(lambda x: abs(x - Qb_Qc))
        branch_row = branch_data.sort_values(by=["Vb/Vc Diff", "Qb/Qc Diff"]).iloc[0]
        C_branch = branch_row["C"]
        branch_loss = C_branch * Pvb

        # --- Main Loss Coefficient Lookup ---
        try:
            df_main = data.loc["A11A"]
            main_data = df_main[(df_main["PATH"] == "main") & (df_main["NAME"] == "Tee or Wye, Main")].copy()
        except KeyError:
            return {"Error": "A11A main data not found in Excel."}

        main_data["Vs/Vc Diff"] = abs(main_data["Vs/Vc"] - Vs_Vc)
        main_row = main_data.sort_values(by="Vs/Vc Diff").iloc[0]
        C_main = main_row["C"]
        main_loss = C_main * Pvs

        # --- Output Dictionary ---
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

A11S_outputs.output_type = "branch_main"
