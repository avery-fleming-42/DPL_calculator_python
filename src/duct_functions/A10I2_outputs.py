import math
import pandas as pd
from data_access import get_case_table


def A10I2_outputs(stored_values, *_):
    """
    Computes outputs for case A10I2 (Symmetrical Rectangular Wye),
    with ANGLE and Qb/Qc filtering and flat dictionary return.

    Returns 4 values for Branch 1, 4 for Branch 2, and 2 for the Main.
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        H = stored_values.get("entry_1")        # Height (in)
        W_branch = stored_values.get("entry_2") # Branch Width (in)
        theta = stored_values.get("entry_3")    # Angle (degrees)
        Q1b = stored_values.get("entry_4")      # Branch 1 Flow Rate (cfm)
        Q2b = stored_values.get("entry_5")      # Branch 2 Flow Rate (cfm)

        if not all([H, W_branch, theta, Q1b, Q2b]):
            return {"Error": "Missing input values. Please enter all required values."}

        # ==========================
        #   GEOMETRY & FLOW
        # ==========================
        # Convert dimensions to feet and compute areas (ft²)
        H_ft = H / 12.0
        W_ft = W_branch / 12.0
        A_branch = H_ft * W_ft
        A_main = 2.0 * A_branch

        # Converged flow rate and velocity
        Qc = Q1b + Q2b
        Vc = Qc / A_main
        VPc = (Vc / 4005.0) ** 2

        # ==========================
        #   LOOKUP DATA
        # ==========================
        try:
            branch_data = get_case_table("A10I2").copy()
        except KeyError:
            return {"Error": "A10I2 lookup table not found."}

        if branch_data.empty:
            return {"Error": "A10I2 lookup table is empty."}

        # ==========================
        #   BRANCH HELPER
        # ==========================
        def compute_branch(qb, branch_label):
            qb_qc_ratio = qb / Qc

            # Filter by ANGLE and Qb/Qc, then sort to pick the closest "up"
            candidates = branch_data[
                (branch_data["ANGLE"] >= theta) &
                (branch_data["Q_1b/Qc or Q_2b/Qc"] >= qb_qc_ratio)
            ].sort_values(by=["ANGLE", "Q_1b/Qc or Q_2b/Qc"])

            if candidates.empty:
                selected = branch_data.iloc[-1]
            else:
                selected = candidates.iloc[0]

            C = selected["C"]
            Vb = qb / A_branch
            VPb = (Vb / 4005.0) ** 2
            P_loss = C * VPb

            return {
                f"{branch_label} Velocity (ft/min)": Vb,
                f"{branch_label} Velocity Pressure (in w.c.)": VPb,
                f"{branch_label} Loss Coefficient": C,
                f"{branch_label} Pressure Loss (in w.c.)": P_loss,
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
        return {"Error": f"Error occurred in A10I2: {e}"}


A10I2_outputs.output_type = "dual_branch"
