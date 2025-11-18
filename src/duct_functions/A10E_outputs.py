import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def A10E_outputs(stored_values, *_):
    """
    Calculates the outputs for case A10E (converging junctions with different diameters).
    Uses circular ducts with full branch/main output format.
    """
    try:
        # --------------------------
        #   INPUTS
        # --------------------------
        D_source = stored_values.get("entry_1")   # Source diameter (in)
        D_converging = stored_values.get("entry_2")  # Converging diameter (in)
        D_branch = stored_values.get("entry_3")   # Branch diameter (in)
        Q_source = stored_values.get("entry_4")   # Source flow rate (cfm)
        Q_branch = stored_values.get("entry_5")   # Branch flow rate (cfm)

        # Validate inputs
        if not all([D_source, D_converging, D_branch, Q_source, Q_branch]):
            return {
                "Error": "Missing input values. Please enter all required values "
                         "(D_source, D_converging, D_branch, Q_source, Q_branch)."
            }

        # --------------------------
        #   GEOMETRY & FLOW
        # --------------------------
        # Areas (ft²) for circular ducts
        A_source = math.pi * (D_source / 2.0) ** 2 / 144.0
        A_converging = math.pi * (D_converging / 2.0) ** 2 / 144.0
        A_branch = math.pi * (D_branch / 2.0) ** 2 / 144.0

        # Velocities (ft/min)
        Vb = Q_branch / A_branch
        Vc = (Q_source + Q_branch) / A_converging
        Vs = Q_source / A_source

        # Velocity pressures (in. w.c.)
        Pvb = (Vb / 4005.0) ** 2
        Pvc = (Vc / 4005.0) ** 2
        Pvs = (Vs / 4005.0) ** 2

        # Ratios for lookup
        As_Ac = A_source / A_converging
        Ab_Ac = A_branch / A_converging
        Qb_Qs = Q_branch / Q_source

        # Enforce minimum Qb/Qs of 0.2 (as in legacy logic)
        if Qb_Qs < 0.2:
            Qb_Qs = 0.2

        # --------------------------
        #   BRANCH LOSS COEFFICIENT
        # --------------------------
        branch_data = get_case_table("A10E")
        branch_data = branch_data[branch_data["PATH"] == "branch"].copy()
        branch_data = branch_data.dropna(subset=["As/Ac", "Ab/Ac", "Qb/Qs", "C"])

        if branch_data.empty:
            return {"Error": "No valid branch data found for A10E."}

        # Legacy inequality pattern:
        # As/Ac >= As_Ac, Ab/Ac <= Ab_Ac, Qb/Qs >= Qb_Qs
        match_branch = branch_data[
            (branch_data["As/Ac"] >= As_Ac) &
            (branch_data["Ab/Ac"] <= Ab_Ac) &
            (branch_data["Qb/Qs"] >= Qb_Qs)
        ]

        if not match_branch.empty:
            branch_loss_coefficient = match_branch.iloc[0]["C"]
        else:
            # Fallback: last row
            branch_loss_coefficient = branch_data.iloc[-1]["C"]

        # --------------------------
        #   MAIN LOSS COEFFICIENT
        # --------------------------
        main_data = get_case_table("A10M")
        main_data = main_data[main_data["PATH"] == "main"].copy()
        main_data = main_data.dropna(subset=["As/Ac", "Ab/Ac", "Qb/Qs", "C"])

        if main_data.empty:
            return {"Error": "No valid main data found for A10M."}

        # Legacy inequality pattern:
        # As/Ac <= As_Ac, Ab/Ac >= Ab_Ac, Qb/Qs <= Qb_Qs
        match_main = main_data[
            (main_data["As/Ac"] <= As_Ac) &
            (main_data["Ab/Ac"] >= Ab_Ac) &
            (main_data["Qb/Qs"] <= Qb_Qs)
        ]

        if not match_main.empty:
            main_loss_coefficient = match_main.iloc[-1]["C"]
        else:
            # Fallback: first row
            main_loss_coefficient = main_data.iloc[0]["C"]

        # --------------------------
        #   PRESSURE LOSSES
        # --------------------------
        branch_pressure_loss = branch_loss_coefficient * Pvb
        main_pressure_loss = main_loss_coefficient * Pvs

        # --------------------------
        #   OUTPUTS
        # --------------------------
        outputs = {
            # Branch
            "Branch Velocity (ft/min)": Vb,
            "Branch Velocity Pressure (in w.c.)": Pvb,
            "Branch Loss Coefficient": branch_loss_coefficient,
            "Branch Pressure Loss (in w.c.)": branch_pressure_loss,

            # Main
            "Main, Source Velocity (ft/min)": Vs,
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Source Velocity Pressure (in w.c.)": Pvs,
            "Main, Converged Velocity Pressure (in w.c.)": Pvc,
            "Main Loss Coefficient": main_loss_coefficient,
            "Main Pressure Loss (in w.c.)": main_pressure_loss,
        }

        return outputs

    except Exception as e:
        return {"Error": str(e)}


A10E_outputs.output_type = "branch_main"
