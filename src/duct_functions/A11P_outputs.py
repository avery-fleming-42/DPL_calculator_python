import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A11P_outputs(inputs, data):
    """
    Calculate outputs for A11P case (rectangular duct diverging).

    Inputs:
        inputs: dict with keys:
            entry_1: Main Height (in),
            entry_2: Main Width (in),
            entry_3: Branch Height (in),
            entry_4: Branch Width (in),
            entry_5: Main Upstream Flow Rate (cfm),
            entry_6: Branch Flow Rate (cfm)
        data: Pandas DataFrame containing the lookup table.

    Returns:
        dict: Output values for branch and main.
    """
    try:
        # Get inputs safely
        H_main = inputs.get("entry_1")
        W_main = inputs.get("entry_2")
        H_branch = inputs.get("entry_3")
        W_branch = inputs.get("entry_4")
        Qc = inputs.get("entry_5")
        Qb = inputs.get("entry_6")

        if None in [H_main, W_main, H_branch, W_branch, Qc, Qb]:
            return {"Error": "Missing input values."}

        # Height warning
        height_warning = None
        if H_branch >= H_main - 2:
            height_warning = "Warning: Branch height should be at least 2 inches smaller than main height."

        # Areas in ft²
        A_main = H_main * W_main / 144
        A_branch = H_branch * W_branch / 144

        # Velocities (fpm)
        Vc = Qc / A_main
        Vs = (Qc - Qb) / A_main
        Vb = Qb / A_branch

        # Velocity pressures (in. wg)
        Pvb = (Vb / 4005) ** 2
        Pvs = (Vs / 4005) ** 2
        Pvc = (Vc / 4005) ** 2

        Vb_Vc = Vb / Vc
        Qb_Qc = Qb / Qc
        Vs_Vc = Vs / Vc

        # --- Branch Coefficient ---
        try:
            df_branch = data.loc["A11P"]
            branch_data = df_branch[df_branch["PATH"] == "branch"].copy()
        except KeyError:
            return {"Error": "A11P branch data not found in Excel."}

        branch_data["Vb/Vc Diff"] = branch_data["Vb/Vc"].apply(lambda x: abs(x - Vb_Vc) if x >= Vb_Vc else float("inf"))
        branch_data["Qb/Qc Diff"] = branch_data["Qb/Qc"].apply(
            lambda x: abs(x - Qb_Qc) if (Qb_Qc < 0.5 and x >= Qb_Qc) or (Qb_Qc >= 0.5 and x <= Qb_Qc) else float("inf")
        )
        branch_row = branch_data.sort_values(by=["Vb/Vc Diff", "Qb/Qc Diff"]).iloc[0]
        C_branch = branch_row["C"]
        branch_loss = C_branch * Pvb

        # --- Main Coefficient (uses A11A main) ---
        try:
            df_main = data.loc["A11A"]
            main_data = df_main[(df_main["PATH"] == "main") & (df_main["NAME"] == "Tee or Wye, Main")].copy()
        except KeyError:
            return {"Error": "A11A main data not found in Excel."}

        main_data["Vs/Vc Diff"] = abs(main_data["Vs/Vc"] - Vs_Vc)
        main_row = main_data.sort_values("Vs/Vc Diff").iloc[0]
        C_main = main_row["C"]
        main_loss = C_main * Pvs

        result = {
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

        if height_warning:
            result["Warning"] = height_warning

        return result

    except Exception as e:
        return {"Error": str(e)}

A11P_outputs.output_type = "branch_main"
