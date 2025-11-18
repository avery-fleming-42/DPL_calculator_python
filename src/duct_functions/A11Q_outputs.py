import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A11Q_outputs(stored_values, *_):
    """
    Calculate outputs for A11Q case (rectangular diverging).

    Inputs:
        stored_values: dict with keys:
            entry_1: Main Height (in)
            entry_2: Main Width (in)
            entry_3: Branch Height (in)
            entry_4: Branch Width (in)
            entry_5: Main Upstream Flow Rate (Qc, cfm)
            entry_6: Branch Flow Rate (Qb, cfm)

    Returns:
        dict: Output values for branch and main (plus optional Warning).
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        H_main = stored_values.get("entry_1")
        W_main = stored_values.get("entry_2")
        H_branch = stored_values.get("entry_3")
        W_branch = stored_values.get("entry_4")
        Qc = stored_values.get("entry_5")
        Qb = stored_values.get("entry_6")

        if None in [H_main, W_main, H_branch, W_branch, Qc, Qb]:
            return {"Error": "Missing input values."}

        # ==========================
        #   HEIGHT WARNING
        # ==========================
        height_warning = None
        if H_branch >= H_main - 2:
            height_warning = (
                "Warning: Branch height should be at least 2 inches smaller than main height."
            )

        # ==========================
        #   GEOMETRY & FLOW
        # ==========================
        # Areas (ft²)
        A_main = H_main * W_main / 144.0
        A_branch = H_branch * W_branch / 144.0

        # Velocities (fpm)
        Vc = Qc / A_main
        Vb = Qb / A_branch
        Vs = (Qc - Qb) / A_main

        # Velocity pressures (in. w.c.)
        Pvb = (Vb / 4005.0) ** 2
        Pvs = (Vs / 4005.0) ** 2
        Pvc = (Vc / 4005.0) ** 2

        # Ratios
        Vb_Vc = Vb / Vc
        Qb_Qc = Qb / Qc
        Vs_Vc = Vs / Vc

        # ==========================
        #   BRANCH LOOKUP (A11Q)
        # ==========================
        try:
            branch_data = get_case_table("A11Q")
            branch_data = branch_data[branch_data["PATH"] == "branch"].copy()
        except KeyError:
            return {"Error": "A11Q branch data not found."}

        if branch_data.empty:
            return {"Error": "No branch data found for A11Q."}

        # Directional matching, same as legacy:
        # - Vb/Vc: only consider rows with Vb/Vc >= current
        # - Qb/Qc: only consider rows with Qb/Qc >= current
        branch_data["Vb/Vc Diff"] = branch_data["Vb/Vc"].apply(
            lambda x: abs(x - Vb_Vc) if x >= Vb_Vc else float("inf")
        )
        branch_data["Qb/Qc Diff"] = branch_data["Qb/Qc"].apply(
            lambda x: abs(x - Qb_Qc) if x >= Qb_Qc else float("inf")
        )

        branch_row = branch_data.sort_values(by=["Vb/Vc Diff", "Qb/Qc Diff"]).iloc[0]
        C_branch = branch_row["C"]
        branch_loss = C_branch * Pvb

        # ==========================
        #   MAIN LOOKUP (A11R main)
        # ==========================
        try:
            main_data = get_case_table("A11R")
            main_data = main_data[main_data["PATH"] == "main"].copy()
        except KeyError:
            return {"Error": "A11R main data not found."}

        if main_data.empty:
            return {"Error": "No main data found for A11R (main path)."}

        main_data["Vs/Vc Diff"] = (main_data["Vs/Vc"] - Vs_Vc).abs()
        main_row = main_data.sort_values("Vs/Vc Diff").iloc[0]
        C_main = main_row["C"]
        main_loss = C_main * Pvs

        # ==========================
        #   OUTPUTS
        # ==========================
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


A11Q_outputs.output_type = "branch_main"
