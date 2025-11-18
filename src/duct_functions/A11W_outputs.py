import math
import pandas as pd
from data_access import get_case_table


def A11W_outputs(stored_values, *_):
    """
    Calculate outputs for A11W case (Symmetrical Dovetail Wye).

    Inputs (stored_values):
        entry_1: Main Height (in)
        entry_2: Main Width (in)
        entry_3: Branch Area / Main Area (dimensionless, dropdown)
        entry_4: Main Upstream Flow Rate Qc (cfm)

    Returns:
        dict: Outputs for Branch 1, Branch 2, and Main.
    """
    try:
        # ==========================
        #   INPUTS
        # ==========================
        H = stored_values.get("entry_1")       # Height (in)
        Wc = stored_values.get("entry_2")      # Width (in)
        area_ratio = stored_values.get("entry_3")  # Branch Area / Main Area
        Qc = stored_values.get("entry_4")      # Total upstream flow (cfm)

        if None in [H, Wc, area_ratio, Qc]:
            return {"Error": "Missing input values."}

        # ==========================
        #   AREAS (ft²)
        # ==========================
        A_main = (H * Wc) / 144.0
        A_branch = area_ratio * A_main  # each branch has this area

        # ==========================
        #   VELOCITIES (ft/min)
        # ==========================
        Vc = Qc / A_main
        # Symmetrical: total branch flow = Qc, each branch gets half
        Vb = (Qc / 2.0) / A_branch

        # ==========================
        #   VELOCITY PRESSURES (in w.c.)
        # ==========================
        VPc = (Vc / 4005.0) ** 2
        VPb = (Vb / 4005.0) ** 2

        # ==========================
        #   BRANCH LOSS COEFFICIENT (A11W)
        # ==========================
        try:
            branch_data = get_case_table("A11W")
        except KeyError:
            return {"Error": "A11W branch data not found."}

        # Ensure numeric for matching column
        branch_data["A_1b/Ac or A_2b/Ac"] = pd.to_numeric(
            branch_data["A_1b/Ac or A_2b/Ac"], errors="coerce"
        )

        branch_match = branch_data[
            branch_data["A_1b/Ac or A_2b/Ac"].round(4) == round(area_ratio, 4)
        ]

        if branch_match.empty:
            return {
                "Error": "No matching branch data found for the selected area ratio."
            }

        C_branch = branch_match.iloc[0]["C"]
        branch_loss = C_branch * VPb

        # ==========================
        #   OUTPUTS
        # ==========================
        result = {
            # Branch 1
            "Branch 1 Velocity (ft/min)": Vb,
            "Branch 1 Velocity Pressure (in w.c.)": VPb,
            "Branch 1 Loss Coefficient": C_branch,
            "Branch 1 Pressure Loss (in w.c.)": branch_loss,
            # Branch 2 (identical)
            "Branch 2 Velocity (ft/min)": Vb,
            "Branch 2 Velocity Pressure (in w.c.)": VPb,
            "Branch 2 Loss Coefficient": C_branch,
            "Branch 2 Pressure Loss (in w.c.)": branch_loss,
            # Main
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Converged Velocity Pressure (in w.c.)": VPc,
        }

        return result

    except Exception as e:
        return {"Error": str(e)}


# Important to let the GUI know this is a dual-branch layout
A11W_outputs.output_type = "dual_branch"
