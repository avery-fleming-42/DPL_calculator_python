# interpolation.py
import numpy as np
import pandas as pd


def idw_interpolate_nd(df: pd.DataFrame,
                       arg_cols,
                       target_vals,
                       value_col="C",
                       k=8,
                       power=2.0):
    """
    Inverse Distance Weighting (IDW) interpolation in N-D argument space.

    Parameters
    ----------
    df : DataFrame
        Must contain columns in `arg_cols` and `value_col`.
    arg_cols : list[str]
        Column names used as arguments (e.g., ["ANGLE", "As/A"]).
    target_vals : list[float]
        Target values in same order as arg_cols.
    value_col : str
        Name of column containing the scalar being interpolated (usually "C").
    k : int
        Max number of nearest neighbors to use.
    power : float
        Distance exponent in IDW; 2.0 is common.

    Returns
    -------
    float
        Interpolated value.
    """
    if len(arg_cols) != len(target_vals):
        raise ValueError("arg_cols and target_vals must be same length")

    # Extract points and values
    pts = df[arg_cols].to_numpy(dtype=float)  # (n, d)
    vals = df[value_col].to_numpy(dtype=float)

    target = np.asarray(target_vals, dtype=float)

    # Distances in argument space
    diffs = pts - target
    dists = np.sqrt(np.sum(diffs ** 2, axis=1))

    # Exact match: just return corresponding C
    zero_mask = dists == 0
    if np.any(zero_mask):
        return float(vals[zero_mask][0])

    # If all distances are zero (degenerate), just return mean
    if np.all(dists == 0):
        return float(vals.mean())

    # Choose k nearest
    k_eff = min(k, len(dists))
    idx = np.argpartition(dists, k_eff - 1)[:k_eff]
    dsel = dists[idx]
    vsel = vals[idx]

    # Avoid divide by zero just in case
    dsel = np.where(dsel == 0, 1e-12, dsel)

    weights = 1.0 / (dsel ** power)
    weights /= weights.sum()

    return float(np.dot(weights, vsel))
