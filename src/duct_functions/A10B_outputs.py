import math
import numpy as np
from data_access import get_case_table


def A10B_outputs(stored_values, *_):
    """
    Calculates outputs for case A10B, handling both branch and main paths.

    Parameters:
    - stored_values: Dictionary containing user inputs (e.g., D_main, D_branch, etc.).

    Returns:
    - Dictionary containing flat outputs for branch and main.
    """

    # --- Inputs ---
    D_main   = stored_values.get("entry_1")  # Diameter of the main (in)
    D_branch = stored_values.get("entry_2")  # Diameter of the branch (in)
    Q_source = stored_values.get("entry_3")  # Flow rate in the main (cfm)
    Q_branch = stored_values.get("entry_4")  # Flow rate in the branch (cfm)

    # Use None-check so 0 is allowed
    if any(v is None for v in [D_main, D_branch, Q_source, Q_branch]):
        return {
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

    # --- Load consolidated case table ---
    df = get_case_table("A10B")

    if "PATH" not in df.columns:
        raise KeyError("A10B table must include a 'PATH' column with 'branch' / 'main'.")

    branch_data = df[df["PATH"].str.lower() == "branch"]
    main_data   = df[df["PATH"].str.lower() == "main"]

    if branch_data.empty or main_data.empty:
        raise ValueError("A10B table must contain both 'branch' and 'main' rows.")

    # --- Geometry & velocities ---
    area_main   = math.pi * (D_main / 2) ** 2 / 144.0
    area_branch = math.pi * (D_branch / 2) ** 2 / 144.0

    Q_converged = Q_source + Q_branch

    velocity_branch    = Q_branch / area_branch
    velocity_source    = Q_source / area_main
    velocity_converged = Q_converged / area_main

    # ============================
    # Branch loss coefficient
    # ============================
    Qb_Qc = Q_branch / Q_converged
    Ab_Ac = area_branch / area_main

    branch_q_data = (
        branch_data[["Qb/Qc", "Ab/Ac", "C"]]
        .dropna()
        .sort_values(by="Qb/Qc")
    )
    valid_branch_q = branch_q_data[branch_q_data["Qb/Qc"] >= Qb_Qc]
    closest_branch_q = valid_branch_q.iloc[0] if not valid_branch_q.empty else branch_q_data.iloc[-1]

    branch_a_data = (
        branch_data[["Ab/Ac", "C"]]
        .dropna()
        .sort_values(by="Ab/Ac")
    )
    valid_branch_a = branch_a_data[branch_a_data["Ab/Ac"] <= Ab_Ac]
    closest_branch_a = valid_branch_a.iloc[-1] if not valid_branch_a.empty else branch_a_data.iloc[0]

    branch_loss_coefficient = closest_branch_q["C"] * closest_branch_a["C"]

    branch_velocity_pressure = (velocity_branch / 4005.0) ** 2
    branch_pressure_loss     = branch_loss_coefficient * branch_velocity_pressure

    # ============================
    # Main loss coefficient
    # ============================
    Qb_Qc_main = Q_branch / Q_converged

    main_q_data = (
        main_data[["Qb/Qc", "C"]]
        .dropna()
        .sort_values(by="Qb/Qc")
    )
    valid_main_q = main_q_data[main_q_data["Qb/Qc"] >= Qb_Qc_main]
    closest_main_q = valid_main_q.iloc[0] if not valid_main_q.empty else main_q_data.iloc[-1]

    main_loss_coefficient = closest_main_q["C"]

    source_velocity_pressure    = (velocity_source / 4005.0) ** 2
    converged_velocity_pressure = (velocity_converged / 4005.0) ** 2
    main_pressure_loss          = main_loss_coefficient * source_velocity_pressure

    # --- Pack outputs flat (matches your OUTPUT_KEY map) ---
    return {
        # Branch
        "Branch Velocity (ft/min)": velocity_branch,
        "Branch Velocity Pressure (in w.c.)": branch_velocity_pressure,
        "Branch Loss Coefficient": branch_loss_coefficient,
        "Branch Pressure Loss (in w.c.)": branch_pressure_loss,
        # Main
        "Main, Source Velocity (ft/min)": velocity_source,
        "Main, Converged Velocity (ft/min)": velocity_converged,
        "Main, Source Velocity Pressure (in w.c.)": source_velocity_pressure,
        "Main, Converged Velocity Pressure (in w.c.)": converged_velocity_pressure,
        "Main Loss Coefficient": main_loss_coefficient,
        "Main Pressure Loss (in w.c.)": main_pressure_loss,
    }


A10B_outputs.output_type = "branch_main"