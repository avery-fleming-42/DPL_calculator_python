# interpolation_manager.py

import math
from dataclasses import dataclass
from typing import Callable, Dict, Tuple, Optional

import numpy as np
import pandas as pd

from data_access import get_case_table


# ---------- Core IDW interpolation helpers ----------

def _idw_weights_1d(x_data: np.ndarray, xq: float, power: float = 2.0) -> np.ndarray:
    """
    Internal helper: compute IDW weights for 1D scattered data.
    """
    dx = np.abs(x_data - xq)
    # Exact hit? return one-hot
    zero_mask = dx == 0
    if np.any(zero_mask):
        w = np.zeros_like(dx, dtype=float)
        w[zero_mask] = 1.0
        return w
    # Inverse distance weights
    w = 1.0 / (dx ** power)
    w_sum = np.sum(w)
    if w_sum == 0:
        # Fallback: uniform
        return np.ones_like(dx) / len(dx)
    return w / w_sum


def _idw_weights_2d(
    x_data: np.ndarray,
    y_data: np.ndarray,
    xq: float,
    yq: float,
    power: float = 2.0,
) -> np.ndarray:
    """
    Internal helper: compute IDW weights for 2D scattered data.
    """
    dx = x_data - xq
    dy = y_data - yq
    dist = np.sqrt(dx * dx + dy * dy)

    zero_mask = dist == 0
    if np.any(zero_mask):
        w = np.zeros_like(dist, dtype=float)
        w[zero_mask] = 1.0
        return w

    w = 1.0 / (dist ** power)
    w_sum = np.sum(w)
    if w_sum == 0:
        return np.ones_like(dist) / len(dist)
    return w / w_sum


# ---------- Interpolator objects ----------

@dataclass
class Interpolator1D:
    """
    Generic 1D interpolator for scattered data using IDW.
    Stores the data needed for both evaluation and plotting.
    """
    x: np.ndarray           # 1D inputs
    c: np.ndarray           # scalar outputs (e.g., C)
    power: float = 2.0

    def __call__(self, xq: float) -> float:
        w = _idw_weights_1d(self.x, xq, self.power)
        return float(np.sum(w * self.c))

    def grid(self, num_points: int = 200) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns grid_x, grid_c for plotting.
        """
        xmin, xmax = float(self.x.min()), float(self.x.max())
        grid_x = np.linspace(xmin, xmax, num_points)
        grid_c = np.array([self(xi) for xi in grid_x], dtype=float)
        return grid_x, grid_c


@dataclass
class Interpolator2D:
    """
    Generic 2D interpolator for scattered data using IDW.
    Stores the data and can generate a plotting surface.
    """
    x: np.ndarray           # first input dimension, e.g. ANGLE
    y: np.ndarray           # second input dimension, e.g. As/A
    c: np.ndarray           # scalar outputs (e.g., C)
    power: float = 2.0

    def __call__(self, xq: float, yq: float) -> float:
        w = _idw_weights_2d(self.x, self.y, xq, yq, self.power)
        return float(np.sum(w * self.c))

    def grid(
        self,
        num_x: int = 60,
        num_y: int = 60,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns Xgrid, Ygrid, Cgrid for plotting.
        """
        xmin, xmax = float(self.x.min()), float(self.x.max())
        ymin, ymax = float(self.y.min()), float(self.y.max())

        Xg, Yg = np.meshgrid(
            np.linspace(xmin, xmax, num_x),
            np.linspace(ymin, ymax, num_y),
        )
        Cg = np.zeros_like(Xg, dtype=float)
        for i in range(Xg.shape[0]):
            for j in range(Xg.shape[1]):
                Cg[i, j] = self(Xg[i, j], Yg[i, j])
        return Xg, Yg, Cg


# ---------- Registry & preload API ----------

# Global registry, populated at startup.
_CASE_INTERPOLATORS: Dict[str, Dict[str, object]] = {}


def get_case_interpolator(case_name: str) -> Optional[Dict[str, object]]:
    """
    Accessor for the preloaded interpolator bundle for a given case.
    Returns a dict like:
        {
            "interp": Interpolator1D or Interpolator2D,
            "raw_df": pandas.DataFrame (original cleaned table),
            "meta": {... optional metadata ...}
        }
    or None if the case has not been preloaded.
    """
    return _CASE_INTERPOLATORS.get(case_name)


# ---------- Case-specific builder: A13C (Rectangular conical exit) ----------

def _build_A13C_interpolator() -> Dict[str, object]:
    """
    Build a 2D interpolator for A13C:
        inputs:  ANGLE, As/A
        output:  C
    """
    df = get_case_table("A13C").copy()
    df = df[["ANGLE", "As/A", "C"]].dropna()

    # Raw numpy arrays for scattered interpolation
    angle_vals = df["ANGLE"].to_numpy(dtype=float)
    ratio_vals = df["As/A"].to_numpy(dtype=float)
    c_vals = df["C"].to_numpy(dtype=float)

    interp = Interpolator2D(
        x=angle_vals,
        y=ratio_vals,
        c=c_vals,
        power=2.0,  # IDW exponent; adjust if you want smoother/steeper influence
    )

    # Precompute a “nice” grid for plotting in the details UI
    Xg, Yg, Cg = interp.grid(num_x=60, num_y=60)

    # Optionally keep the original df for showing exact table ranges
    return {
        "interp": interp,
        "raw_df": df,
        "grid": (Xg, Yg, Cg),
        "meta": {
            "x_label": "ANGLE (deg)",
            "y_label": "As/A",
            "c_label": "Loss Coefficient C",
        },
    }


# ---------- Main preload entrypoint ----------

def preload_all_case_interpolators():
    """
    Call this once at application startup.
    It populates _CASE_INTERPOLATORS for all cases that have
    an interpolation definition.

    You can extend this by adding more _build_*_interpolator
    functions and registering them here.
    """
    global _CASE_INTERPOLATORS

    registry: Dict[str, Dict[str, object]] = {}

    # A13C surface (ANGLE, As/A -> C)
    try:
        registry["A13C"] = _build_A13C_interpolator()
    except Exception as e:
        # Fail gracefully: don't kill app, but omit this case
        print(f"[WARN] Failed to build A13C interpolator: {e}")

    # TODO: add more cases as you migrate them, e.g.:
    # registry["A13B"] = _build_A13B_interpolator()
    # registry["A12A1"] = _build_A12A1_interpolator()
    # ...

    _CASE_INTERPOLATORS = registry
    print(f"[INFO] Interpolators preloaded for cases: {list(_CASE_INTERPOLATORS.keys())}")
