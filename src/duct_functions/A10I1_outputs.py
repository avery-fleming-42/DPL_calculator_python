import math
import pandas as pd
from data_access import get_case_table


def A10I1_outputs(stored_values, *_):
    """
    Computes outputs for case A10I1 (Symmetrical Round Wye).

    Returns 4 values for Branch 1, 4 for Branch 2, and 2 for the Main.
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        D_branch = stored_values.get("entry_1")  # Diameter of each branch (in)
        theta = stored_values.get("entry_2")     # Angle (degrees)
        Q1b = stored_values.get("entry_3")       # Flow rate in Branch 1 (cfm)
        Q2b = stored_values.get("entry_4")       # Flow rate in Branch 2 (cfm)

        if not all([D_branch, theta, Q1b, Q2b]):
            return {"Error": "Missing input values. Please enter all required values."}

        # ==========================
        #   GEOMETRY & FLOW
        # ==========================
        # Diameter in feet and areas (ft²)
        D_branch_ft = D_branch / 12.0
        A_branch = math.pi * (D_branch_ft / 2.0) ** 2
        A_main = 2.0 * A_branch

        Qc = Q1b + Q2b  # converged flow

        # Main velocity and velocity pressure
        Vc = Qc / A_main
        VPc = (Vc / 4005.0) ** 2

        # ==========================
        #   LOOKUP DATA
        # ==========================
        try:
            branch_data = get_case_table("A10I1").copy()
        except KeyError:
            return {"Error": "A10I1 lookup table not found."}

        if branch_data.empty:
            return {"Error": "A10I1 lookup table is empty."}

        # ==========================
        #   BRANCH HELPER
        # ==========================
        def compute_branch(qb, label):
            qb_qc_ratio = qb / Qc

            # Match rows with ANGLE >= theta and Q_1b/Qc or Q_2b/Qc >= qb_qc_ratio
            valid_rows = branch_data[
                (branch_data["ANGLE"] >= theta) &
                (branch_data["Q_1b/Qc or Q_2b/Qc"] >= qb_qc_ratio)
            ]

            if valid_rows.empty:
                # Fallback: last row if no match found
                selected_row = branch_data.iloc[-1]
            else:
                # Sort by ANGLE then ratio and take the first (closest up)
                selected_row = valid_rows.sort_values(
                    by=["ANGLE", "Q_1b/Qc or Q_2b/Qc"]
                ).iloc[0]

            C = selected_row["C"]

            Vb = qb / A_branch
            VPb = (Vb / 4005.0) ** 2
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
        branch1_outputs = compute_branch(Q1b, "Branch 1")
        branch2_outputs = compute_branch(Q2b, "Branch 2")

        main_outputs = {
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Converged Velocity Pressure (in w.c.)": VPc,
        }

        outputs = {}
        outputs.update(branch1_outputs)
        outputs.update(branch2_outputs)
        outputs.update(main_outputs)

        return outputs

    except Exception as e:
        return {"Error": f"Error occurred in A10I1: {e}"}


A10I1_outputs.output_type = "dual_branch"
