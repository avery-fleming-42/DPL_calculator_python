import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A11T_outputs(stored_values, *_):
    """
    Calculate outputs for A11T case (diverging 90° tap with variable main/branch geometry).

    Inputs:
        stored_values: dict with keys:
            entry_1: Height (in)
            entry_2: Main Upstream Width (in)
            entry_3: Branch Width (in)
            entry_4: Main Upstream Flow Rate (Qc, cfm)
            entry_5: Branch Flow Rate (Qb, cfm)
            entry_6: Angle (degrees)

    Returns:
        dict: Output values for branch and main.
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        H = stored_values.get("entry_1")
        W_main = stored_values.get("entry_2")
        W_branch = stored_values.get("entry_3")
        Qc = stored_values.get("entry_4")
        Qb = stored_values.get("entry_5")
        angle = stored_values.get("entry_6")

        if None in [H, W_main, W_branch, Qc, Qb, angle]:
            return {"Error": "Missing input values."}

        # ==========================
        #   AREAS (ft²)
        # ==========================
        A_main = (H * W_main) / 144.0
        A_branch = (H * W_branch) / 144.0
        A_source = (H * (W_main - W_branch)) / 144.0

        # Guard against degenerate geometry
        if A_source <= 0:
            return {"Error": "Invalid geometry: source area (As) must be positive."}

        # ==========================
        #   VELOCITIES (ft/min)
        # ==========================
        Vc = Qc / A_main
        Vb = Qb / A_branch
        Vs = (Qc - Qb) / A_source

        # ==========================
        #   VELOCITY PRESSURES (in w.c.)
        # ==========================
        Pvb = (Vb / 4005.0) ** 2
        Pvs = (Vs / 4005.0) ** 2
        Pvc = (Vc / 4005.0) ** 2

        # Ratios
        Vb_Vc = Vb / Vc
        Vs_Vc = Vs / Vc
        As_Ac = A_source / A_main

        # ==========================
        #   LOAD CASE TABLE
        # ==========================
        try:
            df = get_case_table("A11T")
        except KeyError:
            return {"Error": "A11T data not found."}

        # ==========================
        #   BRANCH LOSS COEFFICIENT: C_branch = f(angle, Vb/Vc)
        # ==========================
        branch_data = df[(df["PATH"] == "branch") & (df["ANGLE"] == angle)].copy()
        if branch_data.empty:
            return {"Error": f"No branch data in A11T for ANGLE = {angle}°."}

        branch_data["Vb/Vc Diff"] = (branch_data["Vb/Vc"] - Vb_Vc).abs()
        branch_row = branch_data.sort_values("Vb/Vc Diff").iloc[0]
        C_branch = branch_row["C"]
        branch_loss = C_branch * Pvb

        # ==========================
        #   MAIN LOSS COEFFICIENT: C_main = f(Vs/Vc, As/Ac)
        # ==========================
        main_data = df[df["PATH"] == "main"].copy()
        if main_data.empty:
            return {"Error": "No main data found for A11T."}

        # Angle grouping
        if angle in [15, 30, 45, 60]:
            main_data = main_data[main_data["ANGLE"] == "15-60"]
        elif angle == 90:
            main_data = main_data[main_data["ANGLE"] == "90"]

            # As/Ac band selection (string-coded bins, per legacy logic)
            if As_Ac <= 0.4:
                main_data = main_data[main_data["As/Ac"] == "0-0.4"]
            elif 0.4 < As_Ac < 0.5:
                main_data = main_data[main_data["As/Ac"] == "0.5"]
            elif 0.5 < As_Ac < 0.6:
                main_data = main_data[main_data["As/Ac"] == "0.6"]
            elif 0.6 < As_Ac < 0.7:
                main_data = main_data[main_data["As/Ac"] == "0.7"]
            elif As_Ac >= 0.8:
                main_data = main_data[main_data["As/Ac"] == ">=0.8"]

        if main_data.empty:
            return {
                "Error": "No matching main data after ANGLE and As/Ac filtering "
                         f"(ANGLE={angle}, As/Ac≈{As_Ac:.3f})."
            }

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


A11T_outputs.output_type = "branch_main"
