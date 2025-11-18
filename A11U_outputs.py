import math
import pandas as pd
import numpy as np

def A11U_outputs(inputs, data):
    """
    Calculate outputs for A11U case (rectangular main and circular branch).
    """
    try:
        # Extract inputs
        W_main = inputs.get("entry_1")
        H_main = inputs.get("entry_2")
        D_branch = inputs.get("entry_3")
        Qc = inputs.get("entry_4")
        Qb = inputs.get("entry_5")

        if None in [W_main, H_main, D_branch, Qc, Qb]:
            return {"Error": "Missing input values."}

        # Optional warning
        warning_message = None
        if D_branch >= (W_main - 2):
            warning_message = "Warning: Branch diameter should be at least 2 inches smaller than main width."

        # Area calculations (ft²)
        A_main = (W_main * H_main) / 144
        A_branch = math.pi * (D_branch / 24) ** 2  # D/2 then squared

        # Velocities (ft/min)
        Vc = Qc / A_main
        Vb = Qb / A_branch
        Vs = (Qc - Qb) / A_main

        # Velocity pressures (in w.c.)
        Pvb = (Vb / 4005) ** 2
        Pvs = (Vs / 4005) ** 2
        Pvc = (Vc / 4005) ** 2

        # Load branch and main data properly
        try:
            df_A11U = data.loc[["A11U"]]
            df_A11A = data.loc[["A11A"]]
        except KeyError:
            return {"Error": "Required A11U or A11A data not found."}

        # --- Branch Loss Coefficient ---
        branch_data = df_A11U[df_A11U["PATH"] == "branch"].copy()
        Vb_Vc = Vb / Vc
        branch_data["Vb/Vc Diff"] = abs(branch_data["Vb/Vc"] - Vb_Vc)
        branch_row = branch_data.sort_values("Vb/Vc Diff").iloc[0]
        C_branch = branch_row["C"]
        branch_loss = C_branch * Pvb

        # --- Main Loss Coefficient ---
        main_data = df_A11A[(df_A11A["PATH"] == "main") & (df_A11A["NAME"] == "Tee or Wye, Main")].copy()
        Vs_Vc = Vs / Vc
        main_data["Vs/Vc Diff"] = abs(main_data["Vs/Vc"] - Vs_Vc)
        main_row = main_data.sort_values("Vs/Vc Diff").iloc[0]
        C_main = main_row["C"]
        main_loss = C_main * Pvs

        # --- Outputs ---
        result = {
            # Branch Outputs
            "Branch Velocity (ft/min)": Vb,
            "Branch Velocity Pressure (in w.c.)": Pvb,
            "Branch Loss Coefficient": C_branch,
            "Branch Pressure Loss (in w.c.)": branch_loss,
            # Main Outputs
            "Main, Source Velocity (ft/min)": Vs,
            "Main, Converged Velocity (ft/min)": Vc,
            "Main, Source Velocity Pressure (in w.c.)": Pvs,
            "Main, Converged Velocity Pressure (in w.c.)": Pvc,
            "Main Loss Coefficient": C_main,
            "Main Pressure Loss (in w.c.)": main_loss,
        }

        if warning_message:
            result["Warning"] = warning_message

        return result

    except Exception as e:
        return {"Error": f"Error in A11U: {e}"}

# Required to detect branch_main format
A11U_outputs.output_type = "branch_main"
