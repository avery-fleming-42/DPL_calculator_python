import math
import pandas as pd
from data_access import get_case_table


def A11X_outputs(stored_values, *_):
    """
    Computes outputs for case A11X (Symmetrical Wye - Rectangular).
    Returns 4 outputs for Branch 1, 4 for Branch 2, and 2 for the Main.

    Inputs (stored_values):
        entry_1: Height (in)
        entry_2: Main Width (in)
        entry_3: Angle (deg)
        entry_4: Branch 1 Flow (cfm)
        entry_5: Branch 2 Flow (cfm)
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        H = stored_values.get("entry_1")    # Height (in)
        Wc = stored_values.get("entry_2")   # Main Width (in)
        theta = stored_values.get("entry_3")  # Angle (deg)
        Qb1 = stored_values.get("entry_4")  # Branch 1 Flow (cfm)
        Qb2 = stored_values.get("entry_5")  # Branch 2 Flow (cfm)

        if not all([H, Wc, theta, Qb1, Qb2]):
            return {"Error": "Missing input values. Please enter all required values."}

        # ==========================
        #   GEOMETRY & FLOW
        # ==========================
        H_ft = H / 12.0
        Wc_ft = Wc / 12.0
        A_main = H_ft * Wc_ft
        A_branch = A_main / 2.0
        Qc = Qb1 + Qb2

        # Velocities and main VP
        Vc = Qc / A_main
        VPc = (Vc / 4005.0) ** 2

        # ==========================
        #   LOAD CASE TABLE
        # ==========================
        try:
            case_data = get_case_table("A11X")
        except KeyError:
            return {"Error": "A11X data not found."}

        # ==========================
        #   BRANCH HELPER
        # ==========================
        def compute_branch(qb, label):
            Vb = qb / A_branch
            VPb = (Vb / 4005.0) ** 2
            Vb_Vc = Vb / Vc

            # Filter by angle and velocity ratio
            branch_data = case_data.copy()
            branch_filtered = branch_data[
                (branch_data["ANGLE"] >= theta)
                & (branch_data["V_1b/Vc or V_2b/Vc"] >= Vb_Vc)
            ]

            if branch_filtered.empty:
                row = branch_data.iloc[-1]
            else:
                row = branch_filtered.sort_values(
                    by=["ANGLE", "V_1b/Vc or V_2b/Vc"]
                ).iloc[0]

            C = row["C"]
            P_loss = C * VPb

            return {
                f"{label} Velocity (ft/min)": Vb,
                f"{label} Velocity Pressure (in w.c.)": VPb,
                f"{label} Loss Coefficient": C,
                f"{label} Pressure Loss (in w.c.)": P_loss,
            }

        # ==========================
        #   OUTPUTS
        # ==========================
        branch1_outputs = compute_branch(Qb1, "Branch 1")
        branch2_outputs = compute_branch(Qb2, "Branch 2")
        main_outputs = {
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Converged Velocity Pressure (in w.c.)": VPc,
        }

        return {**branch1_outputs, **branch2_outputs, **main_outputs}

    except Exception as e:
        return {"Error": str(e)}


A11X_outputs.output_type = "dual_branch"
