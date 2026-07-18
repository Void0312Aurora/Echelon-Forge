import math

import numpy as np
from python.angles import bearing_deg, wrap_signed_deg
from python.rl.tasking.bridge import mission_command_view


def get_runway_local_frame(loader, x_m: float, y_m: float):
    """
    Returns a geometry-only runway frame derived from the nearest ILS beacon.

    Output:
      valid: bool
      along_m: float  (positive along runway forward axis, relative to runway center)
      cross_m: float  (positive to the runway right)
      length_m: float
      width_m: float
    """
    frame = loader._query_runway_frame_result(float(x_m), float(y_m))
    if frame is None:
        return False, 0.0, 0.0, 0.0, 0.0
    return (
        bool(frame.valid),
        float(frame.along_m),
        float(frame.cross_m),
        float(frame.length_m),
        float(frame.width_m),
    )


def get_ils_observation(loader, x_m: float, y_m: float, alt_m: float):
    """
    Returns a small navigation observation vector:
    [ils_valid, loc_dev, gs_dev, dme_m]

    - loc_dev, gs_dev are normalized to [-1, 1] using the configured max deflections.
    - dme_m is slant-range distance to the threshold reference point.
    - For landing tasks, glideslope is referenced to a threshold-crossing-height
      point above the runway threshold rather than the threshold pavement itself.
    """
    cmd_view = mission_command_view(loader)
    if loader._spatial_geometry is None:
        return np.zeros((4,), dtype=np.float32)
    try:
        threshold_crossing_height_m = max(0.0, float(cmd_view.float_field("threshold_crossing_height_m", 0.0)))
    except Exception:
        threshold_crossing_height_m = 0.0
    ils = loader._spatial_geometry.query_ils(
        float(x_m),
        float(y_m),
        float(alt_m),
        float(threshold_crossing_height_m),
    )
    return np.array(
        [
            1.0 if bool(ils.valid) else 0.0,
            float(ils.loc_dev),
            float(ils.gs_dev),
            float(ils.dme_m),
        ],
        dtype=np.float32,
    )


# Thin aliases kept for API stability; the implementations are owned by python.angles.
bearing_to_deg = bearing_deg
wrap_angle_deg = wrap_signed_deg


def instrument_scalar(inst, attr_name: str, index: int | None = None, default: float = float("nan")) -> float:
    if inst is None:
        return float(default)
    try:
        value = float(getattr(inst, attr_name))
        if math.isfinite(value):
            return value
    except Exception:
        pass
    if index is not None:
        try:
            value = float(inst[index])
            if math.isfinite(value):
                return value
        except Exception:
            pass
    return float(default)
