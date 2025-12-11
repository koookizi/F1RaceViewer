import numpy as np

# rotates all (x,y) by a given angle (in radians)
def rotate(xy, angle: float):

    # uses a rotation matrix (not standard as coordinate system of FastF1 is flipped, and it is clockwise rotation, not anticlockwise)
    rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                        [-np.sin(angle), np.cos(angle)]])
    return np.matmul(xy, rot_mat)

def normalize_xy(x, y):
    # ensure that they are an array of floats
    x = np.asarray(x, dtype="float64")
    y = np.asarray(y, dtype="float64")

    # mask out NaNs / infs
    mask = np.isfinite(x) & np.isfinite(y)
    if not mask.any():
        # nothing usable, just return zeros so it doesn't crash
        return np.zeros_like(x), np.zeros_like(y)

    # works on a valid subset
    x_valid = x[mask]
    y_valid = y[mask]

    # centers the track using the mean
    # why mean? it gets the centre of a group of points basically
    # if u did (max+min)/2 it will break when the shape isn't symmetrical
    x_center = x_valid.mean()
    y_center = y_valid.mean()
    x = x - x_center # when subtracting the center (mean), it basically centres the data around that
    y = y - y_center

    # to see how wide or tall the track is
    max_extent = max(
        float(x_valid.max() - x_valid.min()),
        float(y_valid.max() - y_valid.min()),
    )

    if not np.isfinite(max_extent) or max_extent == 0.0: # basically, if it were invalid
        # avoid divide-by-zero; keep centered but unscaled
        return x, y

    # now scale x and y to fit roughly in [-1,1]
    x = x / max_extent * 2.0
    y = y / max_extent * 2.0
    return x, y
