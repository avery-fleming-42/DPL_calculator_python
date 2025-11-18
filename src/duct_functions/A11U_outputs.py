import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A11U_outputs(stored_values, *_):
    """
    Calculate outputs for A11U case (rectangular main and circular branch).

    Inputs:
        stored_values: dict with keys:
            entry_1: Main Width (in)
            entry_2: Main Height (in)
            entry_3: Branch Diameter (in)
            entry_4: Main Upstream Flow Rate (Qc, cfm)
            entry_5: Branch Flow Rate (Qb, cfm)

    Returns:
        dict: Output values for branch and main (plus optional Warning).
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        W_main = stored_values.get("entry_1")
        H_main = stored_values.get("entry_2")
        D_branch = stored_values.get("entry_3")
        Qc = stored_values.get("entry_4")
        Qb = stored_values.get("entry_5")

        if None in [W_main, H_main, D_branch, Qc, Qb]:
            return {"Error": "Missing input values."}

        # ==========================
        #   GEOMETRY WARNING
        # ==========================
        warning_message = None
        if D_branch >= (W_main - 2):
            warning_message = (
                "Warning: Branch diameter should be at least 2 inches smaller than main width."
            )

        # ==========================
        #   AREA CALCULATIONS (ft²)
        # ==========================
        A_main = (W_main * H_main) / 144.0
        # D in inches -> feet, radius = D/24 ft, area = π r²
        A_branch = math.pi * (D_branch / 24.0) ** 2

        # ==========================
        #   VELOCITIES (ft/min)
        # ==========================
        Vc = Qc / A_main
        Vb = Qb / A_branch
        Vs = (Qc - Qb) / A_main

        # ==========================
        #   VELOCITY PRESSURES (in w.c.)
        # ==========================
        Pvb = (Vb / 4005.0) ** 2
        Pvs = (Vs / 4005.0) ** 2
        Pvc = (Vc / 4005.0) ** 2

        Vb_Vc = Vb / Vc
        Vs_Vc = Vs / Vc

        # ==========================
        #   BRANCH LOSS COEFFICIENT (A11U)
        # ==========================
        try:
            branch_data = get_case_table("A11U")
            branch_data = branch_data[branch_data["PATH"] == "branch"].copy()
        except KeyError:
            return {"Error": "A11U branch data not found."}

        if branch_data.empty:
            return {"Error": "No branch data found for A11U."}

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
                (main_data["PATH"] == "main")
                & (main_data["NAME"] == "Tee or Wye, Main")
            ].copy()
        except KeyError:
            return {"Error": "A11A main data not found."}

        if main_data.empty:
            return {"Error": "No main data found for A11A (Tee or Wye, Main)."}

        main_data["Vs/Vc Diff"] = (main_data["Vs/Vc"] - Vs_Vc).abs()
        main_row = main_data.sort_values("Vs/Vc Diff").iloc[0]
        C_main = main_row["C"]
        main_loss = C_main * Pvs

        # ==========================
        #   OUTPUTS
        # ==========================
        result = {
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

        if warning_message:
            result["Warning"] = warning_message

        return result

    except Exception as e:
        return {"Error": f"Error in A11U: {e}"}


A11U_outputs.output_type = "branch_main"
