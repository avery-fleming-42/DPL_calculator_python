import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A11S_outputs(stored_values, *_):
    """
    Calculate outputs for A11S case (Round Branch to Rectangular Main).

    Inputs:
        stored_values: dict with keys:
            entry_1: Main Height (in)
            entry_2: Main Width (in)
            entry_3: Branch Diameter (in)
            entry_4: Main Upstream Flow Rate (Qc, cfm)
            entry_5: Branch Flow Rate (Qb, cfm)

    Returns:
        dict: Output values for branch and main.
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        H_main = stored_values.get("entry_1")   # Main height (in)
        W_main = stored_values.get("entry_2")   # Main width (in)
        D_branch = stored_values.get("entry_3") # Branch diameter (in)
        Qc = stored_values.get("entry_4")       # Main flow (cfm)
        Qb = stored_values.get("entry_5")       # Branch flow (cfm)

        if None in [H_main, W_main, D_branch, Qc, Qb]:
            return {"Error": "Missing input values."}

        # ==========================
        #   AREAS (ft²)
        # ==========================
        A_main = (H_main * W_main) / 144.0
        A_branch = (math.pi * (D_branch / 12.0) ** 2) / 4.0

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

        # Ratios
        Vb_Vc = Vb / Vc
        Qb_Qc = Qb / Qc
        Vs_Vc = Vs / Vc

        # ==========================
        #   BRANCH LOSS COEFFICIENT (A11S)
        # ==========================
        try:
            branch_data = get_case_table("A11S")
            branch_data = branch_data[branch_data["PATH"] == "branch"].copy()
        except KeyError:
            return {"Error": "A11S branch data not found."}

        if branch_data.empty:
            return {"Error": "No branch data found for A11S."}

        # Same directional logic as legacy:
        # - Vb/Vc: only consider rows with table Vb/Vc >= actual
        # - Qb/Qc: absolute difference
        branch_data["Vb/Vc Diff"] = branch_data["Vb/Vc"].apply(
            lambda x: abs(x - Vb_Vc) if x >= Vb_Vc else float("inf")
        )
        branch_data["Qb/Qc Diff"] = branch_data["Qb/Qc"].apply(
            lambda x: abs(x - Qb_Qc)
        )

        branch_row = branch_data.sort_values(by=["Vb/Vc Diff", "Qb/Qc Diff"]).iloc[0]
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


A11S_outputs.output_type = "branch_main"
