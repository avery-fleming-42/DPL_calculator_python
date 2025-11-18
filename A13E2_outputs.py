import math
import pandas as pd


def A13E2_outputs(stored_values, data):
    """
    Calculates the outputs for case A13E2 (rectangular exit), accounting for:
    - exit geometry (R/W and L/W) for base loss coefficient (C)
    - optional screen obstruction with correction factor (C1)
    """

    # Extract inputs
    H = stored_values.get("entry_1")  # height (in)
    W = stored_values.get("entry_2")  # width (in)
    L = stored_values.get("entry_3")  # length (in)
    R = stored_values.get("entry_4")  # radius (in)
    Q = stored_values.get("entry_5")  # flow rate (cfm)
    obstruction = stored_values.get("entry_6")  # "none (open)", "screen"
    n = stored_values.get("entry_7")  # free area ratio (if applicable)

    print("[DEBUG] Inputs:")
    print(f"  H = {H}, W = {W}, L = {L}, R = {R}, Q = {Q}")
    print(f"  obstruction = {obstruction}, n = {n}")

    if None in (H, W, L, R, Q):
        print("[DEBUG] Missing one or more required inputs.")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
        }

    try:
        A = H * W  # in^2
        V = Q / (A / 144)  # ft/min

        R_W = R / W
        L_W = L / W

        print(f"[DEBUG] Computed: R/W = {R_W:.4f}, L/W = {L_W:.4f}, Velocity = {V:.2f}")

        # Lookup base coefficient
        df = data.loc["A13E2"]
        df = df[["R/W", "L/W", "C"]].dropna()

        RW_vals = df["R/W"].unique()
        LW_vals = df["L/W"].unique()

        RW_match = max([val for val in RW_vals if val <= R_W], default=min(RW_vals))
        LW_match = max([val for val in LW_vals if val <= L_W], default=min(LW_vals))

        print(f"[DEBUG] Matching R/W = {RW_match}, L/W = {LW_match}")

        matched_row = df[(df["R/W"] == RW_match) & (df["L/W"] == LW_match)]
        if matched_row.empty:
            return {"Error": "No matching R/W and L/W pair found in data."}

        C = matched_row["C"].values[0]
        print(f"[DEBUG] Base coefficient C = {C}")

        # Obstruction correction
        C1 = 0
        if obstruction == "screen" and n is not None:
            df_screen = data.loc["A14A1"]
            df_screen = df_screen[["n, free area ratio", "C"]].dropna()
            n_vals = df_screen["n, free area ratio"].unique()
            n_match = max([val for val in n_vals if val <= n], default=min(n_vals))
            C1 = df_screen[df_screen["n, free area ratio"] == n_match]["C"].values[0]
            print(f"[DEBUG] Screen C1 = {C1}")

        loss_coefficient = C + C1 if obstruction == "screen" else C
        print(f"[DEBUG] Final Loss Coefficient = {loss_coefficient}")

        vp = (V / 4005) ** 2
        pressure_loss = loss_coefficient * vp

        return {
            "Output 1: Velocity": V,
            "Output 2: Velocity Pressure": vp,
            "Output 3: Loss Coefficient": loss_coefficient,
            "Output 4: Pressure Loss": pressure_loss,
        }

    except Exception as e:
        print(f"[ERROR] Exception occurred during A13E2_outputs calculation: {e}")
        return {
            "Output 1: Velocity": None,
            "Output 2: Velocity Pressure": None,
            "Output 3: Loss Coefficient": None,
            "Output 4: Pressure Loss": None,
            "Error": str(e),
        }


A13E2_outputs.output_type = "standard"