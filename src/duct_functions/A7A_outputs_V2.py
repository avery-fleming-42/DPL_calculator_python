import math
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def build_a7a_interpolators(data):
    """
    Builds interpolation functions for A7A based on R/D → C and ANGLE → K.
    """
    if "A7A" not in data.index:
        raise KeyError("Data must include 'A7A' index for calculations.")
    df = data.loc["A7A"]

    # Interpolator for R/D → C
    df_rd = df[["R/D", "C"]].dropna()
    interp_C = interp1d(df_rd["R/D"], df_rd["C"], fill_value="extrapolate")

    # Interpolator for ANGLE → K
    df_angle = df[["ANGLE", "K"]].dropna()
    interp_K = interp1d(df_angle["ANGLE"], df_angle["K"], fill_value="extrapolate")

    return interp_C, interp_K

def A7A_outputs(stored_values, data, interpolators=None):
    """
    Calculates outputs for case A7A using parametric interpolation.

    Parameters:
    - stored_values: dict of user inputs
    - data: DataFrame containing A7A data
    - interpolators: (optional) prebuilt (interp_C, interp_K)

    Returns:
    - dict of calculated outputs
    """
    # Extract entries
    entry_1 = stored_values.get("entry_1")  # Diameter (in)
    entry_2 = stored_values.get("entry_2")  # R/D
    entry_3 = stored_values.get("entry_3")  # Angle (deg)
    entry_4 = stored_values.get("entry_4")  # Flow rate (cfm)

    # Check inputs
    if not all([entry_1, entry_2, entry_3, entry_4]):
        return {f"Output {i+1}": None for i in range(4)}

    # Load interpolators if needed
    if interpolators is None:
        interp_C, interp_K = build_a7a_interpolators(data)
    else:
        interp_C, interp_K = interpolators

    # Calculate velocity
    area = math.pi * (entry_1 / 2) ** 2  # in²
    velocity = entry_4 / (area / 144)    # ft/min

    # Interpolate C and K
    C_base = interp_C(entry_2)
    K_correction = interp_K(entry_3)

    # Reynolds Number
    reynolds_number = 8.5 * entry_1 * velocity

    # Equivalent diameter (for Reynolds Correction Factor logic)
    equivalent_diameter = 23766.76 * (velocity ** -1.000794)

    # Determine if RNCF correction is needed
    if velocity < (23766.76 / equivalent_diameter):
        # RNCF hardcoded simple lookup
        correction_table = pd.DataFrame(
            {
                "Re_10^4": [1, 2, 3, 4, 6, 8, 10, 14, 20],
                "0.5": [1.40, 1.26, 1.19, 1.14, 1.09, 1.06, 1.04, 1.00, 1.00],
                "0.75": [1.77, 1.64, 1.56, 1.46, 1.38, 1.30, 1.15, 1.00, 1.00],
            }
        ).set_index("Re_10^4")

        re_scaled = reynolds_number / 1e4
        r_d_rounded = "0.5" if entry_2 <= 0.5 else "0.75"

        # Find closest Re
        closest_re = correction_table.index[
            np.searchsorted(correction_table.index, re_scaled, side="right") - 1
        ]
        rnc_factor = correction_table.loc[closest_re, r_d_rounded]
    else:
        rnc_factor = 1.0

    # Final loss coefficient
    loss_coefficient = float(C_base * K_correction * rnc_factor)

    # Velocity pressure
    velocity_pressure = (velocity / 4005) ** 2

    # Pressure loss
    pressure_loss = loss_coefficient * velocity_pressure

    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient": loss_coefficient,
        "Output 4: Pressure Loss (in w.c.)": pressure_loss,
    }
