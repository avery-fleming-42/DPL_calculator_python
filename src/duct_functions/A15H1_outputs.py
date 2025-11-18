import math
import pandas as pd
from data_access import get_case_table

def A15H1_outputs(stored_values, data):
    """
    Calculates outputs for case A15H1 (Obstruction in Round Duct with Protruding Elements).
    """

    D = stored_values.get("entry_1")
    d = stored_values.get("entry_2")
    L = stored_values.get("entry_3")
    y = stored_values.get("entry_4")
    Q = stored_values.get("entry_5")

    print("[DEBUG] Inputs:")
    print(f"  D = {D}, d = {d}, L = {L}, y = {y}, Q = {Q}")

    if None in (D, d, L, y, Q):
        print("[DEBUG] Missing required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None
        }

    try:
        A = math.pi * (D / 2) ** 2   # in²
        V = Q / (A / 144)            # ft/min
        Re = 8.5 * D * V
        S_m = d * L
        Sm_A = S_m / A
        y_D = y / D
        vp = (V / 4005) ** 2

        print(f"[DEBUG] A = {A:.2f}, V = {V:.2f}, Re = {Re:.2f}, S_m/A = {Sm_A:.5f}, y/D = {y_D:.4f}")

        # === Base Loss Coefficient (from A15H1 table)
        df_base = get_case_table("A15H1")[["Re", "S_m/A", "C"]].dropna()

        Re_vals = sorted(df_base["Re"].unique())
        SmA_vals = sorted(df_base["S_m/A"].unique())

        Re_match = max([v for v in Re_vals if v <= Re], default=min(Re_vals))
        SmA_match = min([v for v in SmA_vals if v >= Sm_A], default=max(SmA_vals))

        print(f"[DEBUG] Matched Re = {Re_match}, S_m/A = {SmA_match}")

        row_base = df_base[(df_base["Re"] == Re_match) & (df_base["S_m/A"] == SmA_match)]
        if row_base.empty:
            return {"Error": "No matching Re and S_m/A in A15H1 data."}

        base_C = row_base["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {base_C}")

        # === Correction Factor K (from A15H2 table)
        df_k = get_case_table("A15H2")[["y/D or y/H", "K"]].dropna()

        yD_vals = sorted(df_k["y/D or y/H"].unique())
        yD_match = max([v for v in yD_vals if v <= y_D], default=min(yD_vals))

        K = df_k[df_k["y/D or y/H"] == yD_match]["K"].values[0]
        print(f"[DEBUG] Correction factor K = {K}")

        total_C = K * base_C
        pressure_loss = total_C * vp

        print(f"[DEBUG] Final C = {total_C}, ΔP = {pressure_loss:.5f}")

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": total_C,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception during A15H1_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }

A15H1_outputs.output_type = "standard"
