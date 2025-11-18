import math
import pandas as pd

def A11W_outputs(inputs, data):
    """
    Calculate outputs for A11W case (Symmetrical Dovetail Wye).

    Inputs:
        inputs: dict with keys:
            "entry_1": Main Height (in)
            "entry_2": Main Width (in)
            "entry_3": Branch Area/Main Area (dropdown selection)
            "entry_4": Main Upstream Flow Rate (cfm)
        data: Pandas DataFrame containing lookup tables.

    Returns:
        dict: Outputs for Branch 1, Branch 2, and Main.
    """
    try:
        # Extract inputs
        H = inputs.get("entry_1")  # Height (in)
        Wc = inputs.get("entry_2") # Width (in)
        area_ratio = inputs.get("entry_3")  # Branch Area / Main Area
        Qc = inputs.get("entry_4")  # Total upstream flow rate (cfm)

        if None in [H, Wc, area_ratio, Qc]:
            return {"Error": "Missing input values."}

        # Calculate areas (convert to ft²)
        A_main = (H * Wc) / 144

        # Branch area (ft²)
        A_branch = area_ratio * A_main

        # Velocities (fpm)
        Vc = Qc / A_main
        Vb = (Qc / 2) / A_branch  # Each branch gets half the total branch flow

        # Velocity pressures (in w.c.)
        VPc = (Vc / 4005) ** 2
        VPb = (Vb / 4005) ** 2

        # --- Branch Loss Coefficient ---
        try:
            branch_data = data.loc["A11W"]
        except KeyError:
            return {"Error": "A11W branch data not found in Excel."}

        branch_data["A_1b/Ac or A_2b/Ac"] = pd.to_numeric(branch_data["A_1b/Ac or A_2b/Ac"], errors="coerce")

        branch_match = branch_data[
            branch_data["A_1b/Ac or A_2b/Ac"].round(4) == round(area_ratio, 4)
        ]

        if branch_match.empty:
            return {"Error": "No matching branch data found for the selected area ratio."}

        C_branch = branch_match.iloc[0]["C"]
        branch_loss = C_branch * VPb

        # Outputs
        result = {
            # Branch 1 Outputs
            "Branch 1 Velocity (ft/min)": Vb,
            "Branch 1 Velocity Pressure (in w.c.)": VPb,
            "Branch 1 Loss Coefficient": C_branch,
            "Branch 1 Pressure Loss (in w.c.)": branch_loss,
            # Branch 2 Outputs (same as Branch 1)
            "Branch 2 Velocity (ft/min)": Vb,
            "Branch 2 Velocity Pressure (in w.c.)": VPb,
            "Branch 2 Loss Coefficient": C_branch,
            "Branch 2 Pressure Loss (in w.c.)": branch_loss,
            # Main Outputs (only 2)
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Converged Velocity Pressure (in w.c.)": VPc,
        }

        return result

    except Exception as e:
        return {"Error": str(e)}

# Important to let the GUI know this is a dual-branch layout
A11W_outputs.output_type = "dual_branch"
