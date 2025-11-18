import math
import pandas as pd
from data_access import get_case_table

def A10I2_outputs(inputs, data):
    """
    Computes outputs for case A10I2 (Symmetrical Rectangular Wye),
    with proper ANGLE and Qb/Qc filtering and flat dictionary return.
    """
    try:
        # Extract inputs
        H = inputs.get("entry_1")  # Height (in)
        W_branch = inputs.get("entry_2")  # Branch Width (in)
        theta = inputs.get("entry_3")  # Angle (degrees)
        Q1b = inputs.get("entry_4")  # Branch 1 Flow Rate (cfm)
        Q2b = inputs.get("entry_5")  # Branch 2 Flow Rate (cfm)

        if not all([H, W_branch, theta, Q1b, Q2b]):
            return {f"Output {i+1}": None for i in range(10)}

        # Convert dimensions to feet and calculate areas
        H_ft = H / 12
        W_ft = W_branch / 12
        A_branch = H_ft * W_ft
        A_main = 2 * A_branch

        # Converged flow rate and velocity
        Qc = Q1b + Q2b
        Vc = Qc / A_main
        VPc = (Vc / 4005) ** 2

        # Lookup data for A10I2
        try:
            branch_data = data.loc["A10I2"]
        except KeyError:
            return {"Error": "A10I2 data not found in Excel."}

        def compute_branch(qb, branch_label):
            qb_qc_ratio = qb / Qc

            # Perform dual filtering (ANGLE and Qb/Qc)
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
            VPb = (Vb / 4005) ** 2
            P_loss = C * VPb

            return {
                f"{branch_label} Velocity (ft/min)": Vb,
                f"{branch_label} Velocity Pressure (in w.c.)": VPb,
                f"{branch_label} Loss Coefficient": C,
                f"{branch_label} Pressure Loss (in w.c.)": P_loss,
            }

        # Compute branch outputs
        branch1_outputs = compute_branch(Q1b, "Branch 1")
        branch2_outputs = compute_branch(Q2b, "Branch 2")

        # Compute main outputs
        main_outputs = {
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Converged Velocity Pressure (in w.c.)": VPc,
        }

        # --- Flatten final output ---
        outputs = {}
        outputs.update(branch1_outputs)
        outputs.update(branch2_outputs)
        outputs.update(main_outputs)

        return outputs

    except Exception as e:
        return {"Error": str(e)}

A10I2_outputs.output_type = "dual_branch"
print("[DEBUG] A10I2_outputs module loaded, output_type =", A10I2_outputs.output_type)
