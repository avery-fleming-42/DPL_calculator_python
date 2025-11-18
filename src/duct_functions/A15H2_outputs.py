import math
import pandas as pd
from data_access import get_case_table

def A15H2_outputs(stored_values):
    """
    Calculates outputs for case A15H2 (Obstruction in Rectangular Duct with Protruding Elements).
    Uses:
      - A15H1 (base loss coefficients)
      - A15H2 (correction factors)
    Loaded via get_case_table()
    """

    H = stored_values.get("entry_1")
    L = stored_values.get("entry_2")
    d = stored_values.get("entry_3")
    y = stored_values.get("entry_4")
    Q = stored_values.get("entry_5")

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, L = {L}, d = {d}, y = {y}, Q = {Q}")

    if None in (H, L, d, y, Q):
        print("[DEBUG] Missing required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None
        }

    try:
        # --- Load data tables ---
        base_table = get_case_table("A15H1")[["Re", "S_m/A", "C"]].dropna()
        k_table    = get_case_table("A15H2")[["y/D or y/H", "K"]].dropna()

        # --- Geometry and flow ---
        A = H * L                     # in²
        D_eq = (2 * H * L) / (H + L)  # equivalent hydraulic diameter
        V = Q / (A / 144)             # ft/min
        vp = (V / 4005) ** 2
        Re = 8.5 * D_eq * V
        S_m = d * L
        Sm_A = S_m / A
        y_H = y / H

        print(f"[DEBUG] A = {A:.2f}, D_eq = {D_eq:.2f}, V = {V:.2f}, Re = {Re:.2f}, S_m/A = {Sm_A:.5f}, y/H = {y_H:.4f}")

        # --- Base C lookup (A15H1) ---
        Re_vals = sorted(base_table["Re"].unique())
        SmA_vals = sorted(base_table["S_m/A"].unique())

        Re_match = max([v for v in Re_vals if v <= Re], default=min(Re_vals))
        SmA_match = min([v for v in SmA_vals if v >= Sm_A], default=max(SmA_vals))

        print(f"[DEBUG] Matched Re = {Re_match}, S_m/A = {SmA_match}")

        base_row = base_table[(base_table["Re"] == Re_match) & (base_table["S_m/A"] == SmA_match)]
        if base_row.empty:
            return {"Error": "No matching Re and S_m/A found in A15H1."}

        base_C = base_row["C"].values[0]
        print(f"[DEBUG] Base C = {base_C}")

        # --- Correction factor K lookup (A15H2) ---
        yH_vals = sorted(k_table["y/D or y/H"].unique())
        yH_match = max([v for v in yH_vals if v <= y_H], default=min(yH_vals))

        K = k_table[k_table["y/D or y/H"] == yH_match]["K"].values[0]
        print(f"[DEBUG] Correction factor K = {K}")

        total_C = K * base_C
        pressure_loss = total_C * vp

        print(f"[DEBUG] Final C = {total_C}, ΔP = {pressure_loss:.4f}")

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": total_C,
            "Output 4: Pressure Loss": pressure_loss
        }

    except Exception as e:
        print(f"[ERROR] Exception during A15H2_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e)
        }

A15H2_outputs.output_type = "standard"
