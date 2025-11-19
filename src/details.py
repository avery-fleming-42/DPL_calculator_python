# details.py
import numpy as np
import pandas as pd
from case_registry import CASE_CONFIG
from interpolation import idw_interpolate_nd


def _apply_row_filter(df: pd.DataFrame, row_filter: dict | None) -> pd.DataFrame:
    if not row_filter:
        return df
    out = df
    for col, val in row_filter.items():
        out = out[out[col] == val]
    return out


def get_case_details(case_key: str,
                     data: pd.DataFrame,
                     arg_values: dict | None = None,
                     k: int = 8,
                     power: float = 2.0):
    """
    Build a 'details' payload for a given case.

    Returns a dict with:
      - description
      - excel_range
      - arg_cols
      - value_col
      - raw_data (filtered df)
      - plot_grid (for 1D or 2D visualization)
      - current_point (optional; uses arg_values)
    """
    cfg = CASE_CONFIG[case_key]
    sheet_key = cfg["sheet_key"]
    arg_cols = cfg["arg_cols"]
    value_col = cfg.get("value_col", "C")
    row_filter = cfg.get("row_filter")

    # 1) extract & filter raw data
    df = data.loc[sheet_key].copy()
    df = _apply_row_filter(df, row_filter)
    cols_needed = arg_cols + [value_col]
    df = df[cols_needed].dropna()

    details = {
        "description": cfg.get("description"),
        "excel_range": cfg.get("excel_range"),
        "arg_cols": arg_cols,
        "value_col": value_col,
        "raw_data": df,  # UI can render this as a table
    }

    dim = len(arg_cols)

    # Helper: build full arg list for N-D
    def _full_target_vals(primary_vals: dict):
        vals = []
        for name in arg_cols:
            if name in primary_vals:
                vals.append(primary_vals[name])
            elif arg_values and name in arg_values:
                vals.append(arg_values[name])
            else:
                # fallback: median of that column
                vals.append(float(df[name].median()))
        return vals

    # 2) Build plot grid
    if dim == 1:
        col = arg_cols[0]
        xs = np.linspace(df[col].min(), df[col].max(), 200)
        ys = []
        for x in xs:
            C = idw_interpolate_nd(df, [col], [x],
                                   value_col=value_col,
                                   k=k, power=power)
            ys.append(C)
        details["plot_grid"] = {
            "type": "1d",
            "x_label": col,
            "x": xs.tolist(),
            "y": ys,
        }

    else:
        # Use first two arguments as surface axes; others fixed
        c0, c1 = arg_cols[0], arg_cols[1]

        x_vals = np.linspace(df[c0].min(), df[c0].max(), 60)
        y_vals = np.linspace(df[c1].min(), df[c1].max(), 60)
        X, Y = np.meshgrid(x_vals, y_vals)
        Z = np.zeros_like(X)

        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                primary = {c0: X[i, j], c1: Y[i, j]}
                target_vals = _full_target_vals(primary)
                Z[i, j] = idw_interpolate_nd(
                    df, arg_cols, target_vals,
                    value_col=value_col,
                    k=k, power=power
                )

        details["plot_grid"] = {
            "type": "2d",
            "x_label": c0,
            "y_label": c1,
            "x": x_vals.tolist(),
            "y": y_vals.tolist(),
            "z": Z.tolist(),
        }

    # 3) include current evaluation point, if provided
    if arg_values:
        details["current_point"] = {
            name: float(arg_values[name])
            for name in arg_cols
            if name in arg_values
        }

    return details
