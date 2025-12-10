# geometry.py
import numpy as np

def rotate(xy, angle: float):
    rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                        [-np.sin(angle), np.cos(angle)]])
    return np.matmul(xy, rot_mat)

def normalize_xy(x, y):
    x = np.asarray(x, dtype="float64")
    y = np.asarray(y, dtype="float64")

    # mask out NaNs / infs
    mask = np.isfinite(x) & np.isfinite(y)
    if not mask.any():
        # nothing usable, just return zeros so it doesn't crash
        return np.zeros_like(x), np.zeros_like(y)

    x_valid = x[mask]
    y_valid = y[mask]

    # center on mean of valid points
    x_center = x_valid.mean()
    y_center = y_valid.mean()
    x = x - x_center
    y = y - y_center

    max_extent = max(
        float(x_valid.max() - x_valid.min()),
        float(y_valid.max() - y_valid.min()),
    )

    if not np.isfinite(max_extent) or max_extent == 0.0:
        # avoid divide-by-zero; keep centered but unscaled
        return x, y

    x = x / max_extent * 2.0
    y = y / max_extent * 2.0
    return x, y
