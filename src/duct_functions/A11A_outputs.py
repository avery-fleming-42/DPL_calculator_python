import math
import pandas as pd
from data_access import get_case_table


def A11A_outputs(stored_values, *_):
    """
    Calculate outputs for A11A case (diverging, round Tee/Wye).

    Inputs:
        stored_values: dict with keys:
            entry_1: Main Diameter (in)
            entry_2: Branch Diameter (in)
            entry_3: Angle (degrees)
            entry_4: Converged Flow Rate (Qc, cfm)
            entry_5: Branch Flow Rate (Qb, cfm)

    Returns:
        dict: Output values for branch and main.
    """
    try:
        # -------------------------
        #   INPUTS
        # -------------------------
        D_main = stored_values.get("entry_1")
        D_branch = stored_values.get("entry_2")
        angle = stored_values.get("entry_3")
        Qc = stored_values.get("entry_4")
        Qb = stored_values.get("entry_5")

        if None in [D_main, D_branch, angle, Qc, Qb]:
            return {"Error": "Missing input values."}

        # Ensure angle is an int for the NAME match
        angle = int(angle)

        # -------------------------
        #   GEOMETRY & FLOW
        # -------------------------
        # Areas (ft²)
        A_main = math.pi * (D_main / 12.0 / 2.0) ** 2
        A_branch = math.pi * (D_branch / 12.0 / 2.0) ** 2

        # Velocities (ft/min)
        Vc = Qc / A_main              # Converged velocity
        Vs = (Qc - Qb) / A_main       # Source velocity
        Vb = Qb / A_branch            # Branch velocity

        # Velocity pressures (in. w.c.)
        Pvb = (Vb / 4005.0) ** 2
        Pvs = (Vs / 4005.0) ** 2
        Pvc = (Vc / 4005.0) ** 2

        # -------------------------
        #   BRANCH LOSS COEFFICIENT
        # -------------------------
        angle_name = f"Tee or Wye, {angle}°"

        try:
            branch_data = get_case_table("A11A")
            branch_data = branch_data[
                (branch_data["PATH"] == "branch") &
                (branch_data["NAME"] == angle_name)
            ].copy()
        except KeyError:
            return {"Error": "A11A branch data not found."}

        Ab_Ac = A_branch / A_main
        Qb_Qc = Qb / Qc

        branch_filtered = branch_data[
            (branch_data["Ab/Ac"] >= Ab_Ac) &
            (branch_data["Qb/Qc"] >= Qb_Qc)
        ]

        if not branch_filtered.empty:
            branch_row = branch_filtered.sort_values(by=["Ab/Ac", "Qb/Qc"]).iloc[0]
            C_branch = branch_row["C"]
        else:
            branch_row = None
            C_branch = None

        branch_pressure_loss = C_branch * Pvb if C_branch is not None else None

        # -------------------------
        #   MAIN LOSS COEFFICIENT
        # -------------------------
        try:
            main_data = get_case_table("A11A")
            main_data = main_data[
                (main_data["PATH"] == "main") &
                (main_data["NAME"] == "Tee or Wye, Main")
            ].copy()
        except KeyError:
            return {"Error": "A11A main data not found."}

        Vs_Vc = Vs / Vc

        main_filtered = main_data[main_data["Vs/Vc"] >= Vs_Vc]

        if not main_filtered.empty:
            main_row = main_filtered.sort_values(by="Vs/Vc").iloc[0]
            C_main = main_row["C"]
        else:
            main_row = None
            C_main = None

        main_pressure_loss = C_main * Pvc if C_main is not None else None

        # -------------------------
        #   OUTPUTS
        # -------------------------
        return {
            # Branch
            "Branch Velocity (ft/min)": Vb,
            "Branch Velocity Pressure (in w.c.)": Pvb,
            "Branch Loss Coefficient": C_branch,
            "Branch Pressure Loss (in w.c.)": branch_pressure_loss,
            # Main
            "Main, Source Velocity (ft/min)": Vs,
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Source Velocity Pressure (in w.c.)": Pvs,
            "Main, Converged Velocity Pressure (in w.c.)": Pvc,
            "Main Loss Coefficient": C_main,
            "Main Pressure Loss (in w.c.)": main_pressure_loss,
        }

    except Exception as e:
        return {"Error": str(e)}


A11A_outputs.output_type = "branch_main"
