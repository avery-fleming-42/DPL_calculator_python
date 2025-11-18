import math
import pandas as pd
from data_access import get_case_table

def A11A_outputs(inputs, data):
    """
    Calculate outputs for A11A case.

    Inputs:
        inputs: dict with keys:
            entry_1: Main Diameter (in)
            entry_2: Branch Diameter (in)
            entry_3: Angle (degrees)
            entry_4: Converged Flow Rate (cfm)
            entry_5: Branch Flow Rate (cfm)
        data: Pandas DataFrame containing the lookup table.

    Returns:
        dict: Output values for branch and main.
    """
    try:
        # Extract inputs
        D_main = inputs.get("entry_1")
        D_branch = inputs.get("entry_2")
        angle = int(inputs.get("entry_3"))
        Qc = inputs.get("entry_4")
        Qb = inputs.get("entry_5")

        if None in [D_main, D_branch, angle, Qc, Qb]:
            return {"Error": "Missing input values."}

        # Calculate areas and velocities
        A_main = math.pi * (D_main / 12 / 2) ** 2  # Convert to ft and compute area
        A_branch = math.pi * (D_branch / 12 / 2) ** 2

        Vc = Qc / A_main  # Converged velocity
        Vs = (Qc - Qb) / A_main  # Source velocity
        Vb = Qb / A_branch # branch velocity

        # Velocity pressures
        Pvb = (Vb / 4005) **2
        Pvs = (Vs / 4005) **2
        Pvc = (Vc / 4005) **2

        # Lookup branch loss coefficient
        angle_name = f"Tee or Wye, {angle}°"
        try:
            branch_data = data.loc["A11A"]
            branch_data = branch_data[(branch_data["PATH"] == "branch") & (branch_data["NAME"] == angle_name)]
        except KeyError:
            return {"Error": "A11A branch data not found in Excel."}

        Ab_Ac = A_branch / A_main
        Qb_Qc = Qb / Qc
        branch_filtered = branch_data[(branch_data["Ab/Ac"] >= Ab_Ac) & (branch_data["Qb/Qc"] >= Qb_Qc)]
        branch_row = branch_filtered.sort_values(by=["Ab/Ac", "Qb/Qc"]).iloc[0] if not branch_filtered.empty else None
        C_branch = branch_row["C"] if branch_row is not None else None
        branch_loss = C_branch * Pvb if C_branch is not None else None

        # Lookup main loss coefficient
        try:
            main_data = data.loc["A11A"]
            main_data = main_data[(main_data["PATH"] == "main") & (main_data["NAME"] == "Tee or Wye, Main")]
        except KeyError:
            return {"Error": "A11A main data not found in Excel."}

        Vs_Vc = Vs / Vc
        main_filtered = main_data[main_data["Vs/Vc"] >= Vs_Vc]
        main_row = main_filtered.sort_values(by="Vs/Vc").iloc[0] if not main_filtered.empty else None
        C_main = main_row["C"] if main_row is not None else None
        main_loss = C_main * Pvc if C_main is not None else None

        return {
            "Branch Velocity (ft/min)": Vb,
            "Branch Velocity Pressure (in w.c.)": Pvb,
            "Branch Loss Coefficient": C_branch,
            "Branch Pressure Loss (in w.c.)": branch_loss,
            "Main, Source Velocity (ft/min)": Vs,
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Source Velocity Pressure (in w.c.)": Pvs,
            "Main, Converged Velocity Pressure (in w.c.)": Pvc,
            "Main Loss Coefficient": C_main,
            "Main Pressure Loss (in w.c.)": main_loss
        }

    except Exception as e:
        return {"Error": str(e)}

A11A_outputs.output_type = "branch_main"