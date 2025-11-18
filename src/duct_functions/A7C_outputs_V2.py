import math
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def build_a7c_interpolator(data):
    """
    Builds interpolation function for A7C (Angle → C).
    """
    if "A7C" not in data.index:
        raise KeyError("Data must include 'A7C' index for calculations.")
    df = data.loc["A7C"]

    df_angle = df[["ANGLE", "C"]].dropna()
    interp_C = interp1d(
        df_angle["ANGLE"],
        df_angle["C"],
        kind="linear",
        fill_value="extrapolate"
    )
    return interp_C

def A7C_outputs(stored_values, data, interpolator=None):
    """
    Calculates outputs for case A7C using parametric interpolation.
    """

    # Extract entries
    entry_1 = stored_values.get("entry_1")  # Diameter (in)
    entry_2 = stored_values.get("entry_2")  # Angle (deg)
    entry_3 = stored_values.get("entry_3")  # Flow Rate (cfm)

    if not all([entry_1, entry_2, entry_3]):
        return {f"Output {i+1}": None for i in range(4)}

    # Load interpolator if needed
    if interpolator is None:
        interp_C = build_a7c_interpolator(data)
    else:
        interp_C = interpolator

    # Calculate velocity
    area = math.pi * (entry_1 / 2) ** 2  # in²
    velocity = entry_3 / (area / 144)    # ft/min

    # Reynolds number
    reynolds_number = 8.5 * entry_1 * velocity
    equivalent_diameter = 23766.76 * (velocity ** -1.000794)

    # RNCF correction
    if velocity < (23766.76 / equivalent_diameter):
        correction_table = pd.DataFrame(
            {
                "Re_10^4": [1, 2, 3, 4, 6, 8, 10, 14, 20],
                "0.5": [1.40, 1.26, 1.19, 1.14, 1.09, 1.06, 1.04, 1.00, 1.00],
            }
        ).set_index("Re_10^4")

        re_scaled = reynolds_number / 1e4

        closest_re = correction_table.index[
            np.searchsorted(correction_table.index, re_scaled, side="right") - 1
        ]
        rnc_factor = correction_table.loc[closest_re, "0.5"]
    else:
        rnc_factor = 1.0

    # Interpolate base loss coefficient
    C_base = interp_C(entry_2)
    if C_base is None or np.isnan(C_base):
        return {f"Output {i+1}": None for i in range(4)}

    # Final combined loss coefficient
    loss_coefficient = float(C_base * rnc_factor)

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
