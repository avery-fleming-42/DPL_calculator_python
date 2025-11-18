import math
import numpy as np
from data_access import get_case_table

def A10A1_outputs(stored_values, *_):
    """
    Converging junction: Round Converging Wye (A10A1).

    Calculates branch + main outputs.
    """

    # Extract required entries
    D_main  = stored_values.get("entry_1")  # D_main (in)
    D_branch = stored_values.get("entry_2") # D_branch (in)
    Q_s     = stored_values.get("entry_3")  # Q_s (cfm, source/main)
    Q_b     = stored_values.get("entry_4")  # Q_b (cfm, branch)

    # Validate inputs (None check so 0 isn't treated as missing)
    if any(v is None for v in [D_main, D_branch, Q_s, Q_b]):
        return {  # 4 branch + 6 main = 10 outputs
            "Branch Velocity (ft/min)": None,
            "Branch Velocity Pressure (in w.c.)": None,
            "Branch Loss Coefficient": None,
            "Branch Pressure Loss (in w.c.)": None,
            "Main, Source Velocity (ft/min)": None,
            "Main, Converged Velocity (ft/min)": None,
            "Main, Source Velocity Pressure (in w.c.)": None,
            "Main, Converged Velocity Pressure (in w.c.)": None,
            "Main Loss Coefficient": None,
            "Main Pressure Loss (in w.c.)": None,
        }

    # --- Load cleaned tables ---
    branch_data = get_case_table("A10A1")  # branch table
    main_data   = get_case_table("A10A2")  # main table

    # --- Geometry / areas ---
    area_main   = math.pi * (D_main / 2) ** 2 / 144.0   # ft²
    area_branch = math.pi * (D_branch / 2) ** 2 / 144.0 # ft²

    # --- Velocities ---
    velocity_branch    = Q_b / area_branch
    velocity_source    = Q_s / area_main
    velocity_converged = (Q_s + Q_b) / area_main

    # =====================================================
    # Branch loss coefficient (uses Vb/Vc and Ab/Ac columns)
    # =====================================================
    vb_vc_ratio = velocity_branch / velocity_converged
    ab_ac_ratio = area_branch / area_main

    vb_vc_data = (
        branch_data[["Vb/Vc", "Ab/Ac", "C"]]
        .dropna()
        .sort_values(by=["Vb/Vc", "Ab/Ac"])
    )

    valid_vb_vc = vb_vc_data[vb_vc_data["Vb/Vc"] >= vb_vc_ratio]
    branch_vb_vc_row = valid_vb_vc.iloc[0] if not valid_vb_vc.empty else vb_vc_data.iloc[-1]

    valid_ab_ac = vb_vc_data[vb_vc_data["Ab/Ac"] >= ab_ac_ratio]
    branch_ab_ac_row = valid_ab_ac.iloc[0] if not valid_ab_ac.empty else vb_vc_data.iloc[-1]

    branch_loss_coefficient = branch_ab_ac_row["C"]

    # ==============================================
    # Main loss coefficient (uses Vs/Vc and Ab/Ac)
    # ==============================================
    vs_vc_ratio = velocity_source / velocity_converged

    vs_vc_data = (
        main_data[["Vs/Vc", "Ab/Ac", "C"]]
        .dropna()
        .sort_values(by=["Vs/Vc", "Ab/Ac"])
    )

    valid_vs_vc = vs_vc_data[vs_vc_data["Vs/Vc"] >= vs_vc_ratio]
    main_vs_vc_row = valid_vs_vc.iloc[0] if not valid_vs_vc.empty else vs_vc_data.iloc[-1]

    valid_ab_ac_main = vs_vc_data[vs_vc_data["Ab/Ac"] >= ab_ac_ratio]
    main_ab_ac_row = valid_ab_ac_main.iloc[0] if not valid_ab_ac_main.empty else vs_vc_data.iloc[-1]

    main_loss_coefficient = main_ab_ac_row["C"]

    # --- Pressures ---
    velocity_pressure_branch    = (velocity_branch / 4005.0) ** 2
    velocity_pressure_source    = (velocity_source / 4005.0) ** 2
    velocity_pressure_converged = (velocity_converged / 4005.0) ** 2

    branch_pressure_loss = branch_loss_coefficient * velocity_pressure_branch
    main_pressure_loss   = main_loss_coefficient * velocity_pressure_source

    return {
        # Branch
        "Branch Velocity (ft/min)": velocity_branch,
        "Branch Velocity Pressure (in w.c.)": velocity_pressure_branch,
        "Branch Loss Coefficient": branch_loss_coefficient,
        "Branch Pressure Loss (in w.c.)": branch_pressure_loss,
        # Main
        "Main, Source Velocity (ft/min)": velocity_source,
        "Main, Converged Velocity (ft/min)": velocity_converged,
        "Main, Source Velocity Pressure (in w.c.)": velocity_pressure_source,
        "Main, Converged Velocity Pressure (in w.c.)": velocity_pressure_converged,
        "Main Loss Coefficient": main_loss_coefficient,
        "Main Pressure Loss (in w.c.)": main_pressure_loss,
    }

A10A1_outputs.output_type = "branch_main"
