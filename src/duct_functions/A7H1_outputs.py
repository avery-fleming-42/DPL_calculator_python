import math
import pandas as pd
from data_access import get_case_table

def A7H1_outputs(stored_values, *_):
    """
    A7H1 – Mitered with Single Thickness Turning Vanes (Rectangular).

    Inputs (stored_values):
        entry_1: H (in)
        entry_2: W (in)
        entry_3: R (in)  [optional if S is given]
        entry_4: S (in)  [optional if R is given]
        entry_5: Q (cfm)

    Rules:
        - Velocity V = Q / (W * H / 144)   [ft/min]
        - Loss coefficient C is taken from the A7H1 table:
            * Columns: 'R (in)', 'S (in)', 'V, fpm', 'C'
            * Use either R or S (if both entered, prefer R).
            * For that dimension, choose the nearest R or S in the table.
            * For velocity, round DOWN to the nearest tabulated 'V, fpm'
              (clamped to table min/max).
    """

    # -----------------------------
    #  Extract inputs
    # -----------------------------
    H = stored_values.get("entry_1")      # in
    W = stored_values.get("entry_2")      # in
    R_raw = stored_values.get("entry_3")  # in (optional)
    S_raw = stored_values.get("entry_4")  # in (optional)
    Q = stored_values.get("entry_5")      # cfm

    # Basic validation
    if None in (H, W, Q):
        return {
            "Output 1: Velocity": None,
            "Output 2: Vel. Pres @ V0 (in w.c.)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss (in w.c.)": None,
            "Error": "Missing required inputs: H, W, and Q are required.",
        }

    # Normalize R/S: treat <= 0 as "not entered"
    R_in = R_raw if (R_raw is not None and R_raw > 0) else None
    S_in = S_raw if (S_raw is not None and S_raw > 0) else None

    # If both given, prefer R and ignore S (per “R or S” spec)
    if R_in is not None and S_in is not None:
        # print("[INFO] A7H1: both R and S entered; using R and ignoring S.")
        S_in = None

    # -----------------------------
    #  Compute velocity
    # -----------------------------
    try:
        area_in2 = W * H  # in²
        if area_in2 <= 0:
            raise ValueError("W * H must be positive.")

        V = Q / (area_in2 / 144.0)  # ft/min
    except Exception as e:
        return {
            "Output 1: Velocity": None,
            "Output 2: Vel. Pres @ V0 (in w.c.)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss (in w.c.)": None,
            "Error": f"Failed to compute velocity: {e}",
        }

    try:
        # -----------------------------
        #  Load A7H1 table
        # -----------------------------
        df = get_case_table("A7H1").copy()

        needed_cols = ["R (in)", "S (in)", "V, fpm", "C"]
        for col in needed_cols:
            if col not in df.columns:
                raise KeyError(f"Required column '{col}' not found in A7H1 table.")

        df = df[needed_cols].dropna(subset=["R (in)", "S (in)", "V, fpm", "C"])

        # -----------------------------
        #  Dimension selection (R/S row group)
        # -----------------------------
        def subset_by_nearest(col_name, value):
            sub = df[df[col_name].notna()].copy()
            if sub.empty:
                return sub
            diffs = (sub[col_name] - value).abs()
            min_diff = diffs.min()
            return sub[diffs == min_diff]

        if R_in is not None:
            dim_subset = subset_by_nearest("R (in)", R_in)
        elif S_in is not None:
            dim_subset = subset_by_nearest("S (in)", S_in)
        else:
            return {
                "Output 1: Velocity": None,
                "Output 2: Vel. Pres @ V0 (in w.c.)": None,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss (in w.c.)": None,
                "Error": "You must enter either R or S (at least one must be > 0).",
            }

        if dim_subset is None or dim_subset.empty:
            return {
                "Output 1: Velocity": None,
                "Output 2: Vel. Pres @ V0 (in w.c.)": None,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss (in w.c.)": None,
                "Error": "No matching R/S geometry found in A7H1 table.",
            }

        # -----------------------------
        #  Velocity selection (round down)
        # -----------------------------
        vel_values = sorted(dim_subset["V, fpm"].unique())

        if not vel_values:
            return {
                "Output 1: Velocity": V,
                "Output 2: Vel. Pres @ V0 (in w.c.)": None,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss (in w.c.)": None,
                "Error": "No velocity values found in A7H1 table.",
            }

        if V <= vel_values[0]:
            V_match = vel_values[0]
        elif V >= vel_values[-1]:
            V_match = vel_values[-1]
        else:
            V_match = max(v for v in vel_values if v <= V)

        row = dim_subset[dim_subset["V, fpm"] == V_match]
        if row.empty:
            return {
                "Output 1: Velocity": V,
                "Output 2: Vel. Pres @ V0 (in w.c.)": None,
                "Output 3: Loss Coefficient": None,
                "Output 4: Pressure Loss (in w.c.)": None,
                "Error": (
                    f"No row found for matched velocity {V_match} fpm "
                    "in A7H1 data."
                ),
            }

        C = float(row["C"].iloc[0])

        # -----------------------------
        #  Final outputs
        # -----------------------------
        vp = (V / 4005.0) ** 2  # in w.c.
        pressure_loss = C * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Vel. Pres @ V0 (in w.c.)": vp,
            "Output 3: Loss Coefficient": C,
            "Output 4: Pressure Loss (in w.c.)": pressure_loss,
        }

    except Exception as e:
        return {
            "Output 1: Velocity": None,
            "Output 2: Vel. Pres @ V0 (in w.c.)": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss (in w.c.)": None,
            "Error": str(e),
        }

A7H1_outputs.output_type = "standard"