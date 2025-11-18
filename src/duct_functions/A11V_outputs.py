import math
import pandas as pd
import numpy as np
from data_access import get_case_table

def A11V_outputs(inputs, data):
    """
    Calculate outputs for A11V case.
    """
    try:
        # Extract inputs
        H = inputs.get("entry_1")  # Height (in)
        W_c = inputs.get("entry_2")  # Main Upstream Width (in)
        W_b = inputs.get("entry_3")  # Branch Width (in)
        W_s = inputs.get("entry_4")  # Main Downstream Width (in)
        Q_c = inputs.get("entry_5")  # Upstream Flow (cfm)
        Q_b = inputs.get("entry_6")  # Branch Flow (cfm)

        if None in [H, W_c, W_b, W_s, Q_c, Q_b]:
            return {"Error": "Missing input values."}

        # Area calculations (in² → ft²)
        A_c_in2 = H * W_c
        A_s_in2 = H * W_s
        A_b_in2 = H * W_b
        A_c = A_c_in2 / 144
        A_s = A_s_in2 / 144
        A_b = A_b_in2 / 144

        # Velocities
        V_c = Q_c / A_c
        V_b = Q_b / A_b
        V_s = (Q_c - Q_b) / A_s

        # Velocity Pressures
        Pvc = (V_c / 4005) ** 2
        Pvb = (V_b / 4005) ** 2
        Pvs = (V_s / 4005) ** 2

        # Ratios
        Ab_As = A_b_in2 / A_s_in2
        Ab_Ac = A_b_in2 / A_c_in2
        Qb_Qc = Q_b / Q_c
        Vs_Vc = V_s / V_c

        # --- Branch Loss Coefficient ---
        try:
            branch_data = data.loc["A11V"]
            branch_data = branch_data[branch_data["PATH"] == "branch"].copy()
        except KeyError:
            return {"Error": "A11V branch data not found."}

        branch_data["Ab/As Diff"] = abs(branch_data["Ab/As"] - Ab_As)
        branch_data["Ab/Ac Diff"] = abs(branch_data["Ab/Ac"] - Ab_Ac)
        branch_data["Qb/Qc Diff"] = branch_data["Qb/Qc"].apply(
            lambda x: abs(x - Qb_Qc) if Qb_Qc <= 0.7 else (x - Qb_Qc if x >= Qb_Qc else float("inf"))
        )

        branch_row = branch_data.sort_values(by=["Ab/As Diff", "Ab/Ac Diff", "Qb/Qc Diff"]).iloc[0]
        C_branch = branch_row["C"]
        branch_loss = C_branch * Pvb

        # --- Main Loss Coefficient ---
        try:
            main_data = data.loc["A11V"]
            main_data = main_data[main_data["PATH"] == "main"].copy()
        except KeyError:
            return {"Error": "A11V main data not found."}

        main_data["Ab/As Diff"] = abs(main_data["Ab/As"] - Ab_As)
        main_data["Ab/Ac Diff"] = abs(main_data["Ab/Ac"] - Ab_Ac)
        main_data["Qb/Qc Diff"] = main_data["Qb/Qc"].apply(
            lambda x: abs(x - Qb_Qc) if Qb_Qc <= 0.7 else (x - Qb_Qc if x >= Qb_Qc else float("inf"))
        )

        main_row = main_data.sort_values(by=["Ab/As Diff", "Ab/Ac Diff", "Qb/Qc Diff"]).iloc[0]
        C_main = main_row["C"]
        main_loss = C_main * Pvs

        return {
            # Branch Outputs
            "Branch Velocity (ft/min)": V_b,
            "Branch Velocity Pressure (in w.c.)": Pvb,
            "Branch Loss Coefficient": C_branch,
            "Branch Pressure Loss (in w.c.)": branch_loss,
            # Main Outputs
            "Main, Source Velocity (ft/min)": V_s,
            "Main, Converged Velocity (ft/min)": V_c,
            "Main, Source Velocity Pressure (in w.c.)": Pvs,
            "Main, Converged Velocity Pressure (in w.c.)": Pvc,
            "Main Loss Coefficient": C_main,
            "Main Pressure Loss (in w.c.)": main_loss,
        }

    except Exception as e:
        return {"Error": str(e)}

A11V_outputs.output_type = "branch_main"
