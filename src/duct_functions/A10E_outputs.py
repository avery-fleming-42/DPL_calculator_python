import math
import pandas as pd
import numpy as np

def A10E_outputs(stored_values, data):
    """
    Calculates the outputs for case A10E (converging junctions with different diameters).
    Uses circular ducts with full branch/main output format.
    """
    # Extract entries
    D_source = stored_values.get("entry_1")
    D_converging = stored_values.get("entry_2")
    D_branch = stored_values.get("entry_3")
    Q_source = stored_values.get("entry_4")
    Q_branch = stored_values.get("entry_5")

    if not all([D_source, D_converging, D_branch, Q_source, Q_branch]):
        return {f"Output {i+1}": None for i in range(10)}

    # Calculate areas (ft^2)
    A_source = math.pi * (D_source / 2) ** 2 / 144
    A_converging = math.pi * (D_converging / 2) ** 2 / 144
    A_branch = math.pi * (D_branch / 2) ** 2 / 144

    # Calculate velocities
    Vb = Q_branch / A_branch
    Vc = (Q_source + Q_branch) / A_converging
    Vs = Q_source / A_source

    # Velocity pressures
    Pvb = (Vb / 4005) ** 2
    Pvc = (Vc / 4005) ** 2
    Pvs = (Vs / 4005) ** 2

    # Ratios for lookup
    As_Ac = A_source / A_converging
    Ab_Ac = A_branch / A_converging
    Qb_Qs = Q_branch / Q_source

    if Qb_Qs < 0.2:
        Qb_Qs = 0.2

    # --- Branch Loss Coefficient ---
    try:
        branch_data = data.loc["A10E"]
        branch_data = branch_data[branch_data["PATH"] == "branch"]
        branch_data = branch_data.dropna(subset=["As/Ac", "Ab/Ac", "Qb/Qs", "C"])
    except KeyError:
        return {"Error": "A10E branch data not found in Excel."}

    match = branch_data[(branch_data["As/Ac"] >= As_Ac) &
                        (branch_data["Ab/Ac"] <= Ab_Ac) &
                        (branch_data["Qb/Qs"] >= Qb_Qs)]

    if not match.empty:
        branch_loss_coefficient = match.iloc[0]["C"]
    else:
        branch_loss_coefficient = branch_data.iloc[-1]["C"]  # fallback

    # --- Main Loss Coefficient ---
    try:
        main_data = data.loc["A10M"]
        main_data = main_data[main_data["PATH"] == "main"]
        main_data = main_data.dropna(subset=["As/Ac", "Ab/Ac", "Qb/Qs", "C"])
    except KeyError:
        return {"Error": "A10M main data not found in Excel."}

    match_main = main_data[(main_data["As/Ac"] <= As_Ac) &
                           (main_data["Ab/Ac"] >= Ab_Ac) &
                           (main_data["Qb/Qs"] <= Qb_Qs)]

    if not match_main.empty:
        main_loss_coefficient = match_main.iloc[-1]["C"]
    else:
        main_loss_coefficient = main_data.iloc[0]["C"]  # fallback

    # Calculate pressure losses
    branch_pressure_loss = branch_loss_coefficient * Pvb
    main_pressure_loss = main_loss_coefficient * Pvs

    # Return full 10-output format
    return {
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
A10E_outputs.output_type = "branch_main"