import math
import pandas as pd

def A10I1_outputs(inputs, data):
    """
    Computes outputs for case A10I1 (Symmetrical Round Wye).

    Returns 4 values for Branch 1, 4 for Branch 2, and 2 for the Main.
    """
    try:
        # Extract inputs
        D_branch = inputs.get("entry_1")  # Diameter of each branch (in)
        theta = inputs.get("entry_2")     # Angle (degrees)
        Q1b = inputs.get("entry_3")       # Flow rate in Branch 1 (cfm)
        Q2b = inputs.get("entry_4")       # Flow rate in Branch 2 (cfm)

        if not all([D_branch, theta, Q1b, Q2b]):
            return {"Error": "Missing input values. Please enter all required values."}

        # Convert diameter to feet and calculate areas (ft²)
        D_branch_ft = D_branch / 12
        A_branch = math.pi * (D_branch_ft / 2) ** 2
        A_main = 2 * A_branch
        Qc = Q1b + Q2b

        # Velocities
        Vc = Qc / A_main
        VPc = (Vc / 4005) ** 2

        # Lookup branch data
        try:
            branch_data = data.loc["A10I1"]
        except KeyError:
            return {"Error": "A10I1 data not found in Excel."}

        # Helper to compute each branch's results
        def compute_branch(qb, label):
            qb_qc_ratio = qb / Qc
            valid_rows = branch_data[
                (branch_data["ANGLE"] >= theta) &
                (branch_data["Q_1b/Qc or Q_2b/Qc"] >= qb_qc_ratio)
            ]
            if valid_rows.empty:
                selected_row = branch_data.iloc[-1]
            else:
                selected_row = valid_rows.sort_values(by=["ANGLE", "Q_1b/Qc or Q_2b/Qc"]).iloc[0]

            C = selected_row["C"]
            Vb = qb / A_branch
            VPb = (Vb / 4005) ** 2
            P_loss = C * VPb

            return {
                f"{label} Velocity (ft/min)": Vb,
                f"{label} Velocity Pressure (in w.c.)": VPb,
                f"{label} Loss Coefficient": C,
                f"{label} Pressure Loss (in w.c.)": P_loss,
            }

        # Compute all outputs
        branch1_outputs = compute_branch(Q1b, "Branch 1")
        branch2_outputs = compute_branch(Q2b, "Branch 2")
        main_outputs = {
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Converged Velocity Pressure (in w.c.)": VPc,
        }

        # Merge outputs into one dictionary
        outputs = {}
        outputs.update(branch1_outputs)
        outputs.update(branch2_outputs)
        outputs.update(main_outputs)

        return outputs

    except Exception as e:
        return {"Error": f"Error occurred in A10I1: {e}"}

A10I1_outputs.output_type = "dual_branch"

