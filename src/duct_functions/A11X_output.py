import math
import pandas as pd
from data_access import get_case_table

def A11X_outputs(inputs, data):
    """
    Computes outputs for case A11X (Symmetrical Wye - Rectangular).
    Returns 4 outputs for Branch 1, 4 for Branch 2, and 2 for the Main.
    """
    try:
        # Extract inputs using consistent 'entry_#' keys
        H = inputs.get("entry_1")  # Height (in)
        Wc = inputs.get("entry_2")  # Main Width (in)
        theta = inputs.get("entry_3")  # Angle (deg)
        Qb1 = inputs.get("entry_4")  # Branch 1 Flow (cfm)
        Qb2 = inputs.get("entry_5")  # Branch 2 Flow (cfm)

        if not all([H, Wc, theta, Qb1, Qb2]):
            return {f"Output {i+1}": None for i in range(10)}

        # Convert to ft^2
        H_ft = H / 12
        Wc_ft = Wc / 12
        A_main = H_ft * Wc_ft
        A_branch = A_main / 2
        Qc = Qb1 + Qb2

        # Velocities and VPs
        Vc = Qc / A_main
        VPc = (Vc / 4005) ** 2

        def compute_branch(qb, label):
            Vb = qb / A_branch
            VPb = (Vb / 4005) ** 2
            Vb_Vc = Vb / Vc

            try:
                branch_data = data.loc["A11X"]
            except KeyError:
                return {"Error": "A11X data not found in Excel."}

            branch_filtered = branch_data[
                (branch_data["ANGLE"] >= theta) &
                (branch_data["V_1b/Vc or V_2b/Vc"] >= Vb_Vc)
            ]

            if branch_filtered.empty:
                row = branch_data.iloc[-1]
            else:
                row = branch_filtered.sort_values(by=["ANGLE", "V_1b/Vc or V_2b/Vc"]).iloc[0]

            C = row["C"]
            P_loss = C * VPb

            return {
                f"{label} Velocity (ft/min)": Vb,
                f"{label} Velocity Pressure (in w.c.)": VPb,
                f"{label} Loss Coefficient": C,
                f"{label} Pressure Loss (in w.c.)": P_loss,
            }

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