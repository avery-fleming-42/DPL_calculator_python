import math
import pandas as pd
import numpy as np
from data_access import get_case_table


def _loss_coeff_nearest(angle_data: pd.DataFrame, angle: float, area_ratio: float) -> float:
    """
    Original SMACNA-style table lookup:
    - pick smallest ANGLE >= angle (or max if none)
    - within that ANGLE, pick smallest A1/A >= area_ratio (or max if none)
    """
    dat = angle_data[["ANGLE", "A1/A", "C"]].dropna().sort_values(by=["ANGLE", "A1/A"])

    # Match ANGLE
    valid_angle = dat[dat["ANGLE"] >= angle]
    if valid_angle.empty:
        chosen_angle = dat["ANGLE"].max()
    else:
        chosen_angle = valid_angle["ANGLE"].iloc[0]

    # Match A1/A within that ANGLE slice
    slice_df = dat[dat["ANGLE"] == chosen_angle].sort_values("A1/A")
    valid_area = slice_df[slice_df["A1/A"] >= area_ratio]
    if valid_area.empty:
        chosen_row = slice_df.iloc[-1]
    else:
        chosen_row = valid_area.iloc[0]

    return float(chosen_row["C"])


def _interp_c_at_angle(angle_data: pd.DataFrame, angle_slice: float, area_ratio: float) -> float:
    """
    1D interpolation in A1/A for a fixed ANGLE.
    Clamps outside the tabulated A1/A range.
    """
    dat = angle_data[["ANGLE", "A1/A", "C"]].dropna()
    slice_df = dat[dat["ANGLE"] == angle_slice].sort_values("A1/A")

    # Failsafe: if this exact ANGLE is missing, fall back to the closest ANGLE.
    if slice_df.empty:
        nearest_angle = dat.iloc[(dat["ANGLE"] - angle_slice).abs().argmin()]["ANGLE"]
        slice_df = dat[dat["ANGLE"] == nearest_angle].sort_values("A1/A")

    x = slice_df["A1/A"].to_numpy()
    y = slice_df["C"].to_numpy()

    if area_ratio <= x[0]:
        return float(y[0])
    if area_ratio >= x[-1]:
        return float(y[-1])

    # Linear interpolation in A1/A
    return float(np.interp(area_ratio, x, y))


def _loss_coeff_bilinear(angle_data: pd.DataFrame, angle: float, area_ratio: float) -> float:
    """
    Bilinear-style interpolation:
    - Linearly interpolate C vs A1/A at the two bounding ANGLEs.
    - Then linearly interpolate between those two C values in ANGLE.
    - ANGLE is clamped outside data range (no extrapolation beyond min/max).
    """
    dat = angle_data[["ANGLE", "A1/A", "C"]].dropna()
    unique_angles = np.sort(dat["ANGLE"].unique())

    # Clamp or find bounding ANGLEs
    if angle <= unique_angles[0]:
        angle_low = angle_high = unique_angles[0]
    elif angle >= unique_angles[-1]:
        angle_low = angle_high = unique_angles[-1]
    else:
        angle_high = unique_angles[unique_angles > angle].min()
        angle_low = unique_angles[unique_angles < angle].max()

    c_low = _interp_c_at_angle(dat, angle_low, area_ratio)
    c_high = _interp_c_at_angle(dat, angle_high, area_ratio)

    if angle_low == angle_high:
        return c_low

    # Linear interpolation in ANGLE
    t = (angle - angle_low) / (angle_high - angle_low)
    return float(c_low + t * (c_high - c_low))


def A8G_outputs(stored_values, *_):
    """
    A8G: Asymmetric at Fan with Sides Straight, Top Level  (rectangular diverging)

    Uses bilinear interpolation for the loss coefficient instead of
    stepwise rounding to the nearest tabulated value, and also reports
    the original "nearest grid point" C for comparison.

    Inputs (stored_values):
        entry_1: H   (in)
        entry_2: H₁  (in)
        entry_3: W   (in)
        entry_4: ANGLE (deg)
        entry_5: Q   (cfm)
    """
    H = stored_values.get("entry_1")
    H1 = stored_values.get("entry_2")
    W = stored_values.get("entry_3")
    angle = stored_values.get("entry_4")
    Q = stored_values.get("entry_5")

    required = (H, H1, W, angle, Q)
    if any(v is None for v in required):
        return {
            "Output 1: Velocity": None,
            "Output 2: Vel. Pres @ V0 (in w.c.)": None,
            "Output 3: Loss Coefficient (nearest)": None,
            "Output 4: Loss Coefficient (bilinear)": None,
            "Output 5: Pressure Loss (in w.c., bilinear)": None,
        }

    df = get_case_table("A8G")
    if not {"ANGLE", "A1/A", "C"}.issubset(df.columns):
        raise KeyError("Data for A8G must include 'ANGLE', 'A1/A', and 'C' columns.")

    angle_data = df[["ANGLE", "A1/A", "C"]].dropna()

    # Areas in ft²
    A = (H * W) / 144.0
    A1 = (H1 * W) / 144.0

    if A <= 0 or A1 <= 0:
        return {
            "Output 1: Velocity": None,
            "Output 2: Vel. Pres @ V0 (in w.c.)": None,
            "Output 3: Loss Coefficient (nearest)": None,
            "Output 4: Loss Coefficient (bilinear)": None,
            "Output 5: Pressure Loss (in w.c., bilinear)": None,
            "Error": "Computed area <= 0; check inputs.",
        }

    area_ratio = A1 / A

    # Velocity (ft/min)
    velocity = Q / A

    # Velocity pressure (in w.c.)
    velocity_pressure = (velocity / 4005.0) ** 2

    # Original stepwise (nearest grid) C
    loss_coeff_nearest = _loss_coeff_nearest(angle_data, angle, area_ratio)

    # New bilinear C
    loss_coeff_bilinear = _loss_coeff_bilinear(angle_data, angle, area_ratio)

    # Pressure loss using bilinear C
    pressure_loss = loss_coeff_bilinear * velocity_pressure

    return {
        "Output 1: Velocity": velocity,
        "Output 2: Vel. Pres @ V0 (in w.c.)": velocity_pressure,
        "Output 3: Loss Coefficient (nearest)": loss_coeff_nearest,
        "Output 4: Loss Coefficient (bilinear)": loss_coeff_bilinear,
        "Output 5: Pressure Loss (in w.c., bilinear)": pressure_loss,
    }


A8G_outputs.output_type = "standard"
