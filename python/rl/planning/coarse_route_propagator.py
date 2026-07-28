from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Mapping, Sequence

from python.angles import distance_m, wrap_heading_deg, wrap_signed_deg

# Local heading wrap preserved as a thin alias; semantics owned by python.angles.
_wrap_deg = wrap_heading_deg


def angle_diff_deg(target_deg: float, source_deg: float) -> float:
    return wrap_signed_deg(float(target_deg) - float(source_deg))


def bearing_deg(x0_m: float, y0_m: float, x1_m: float, y1_m: float) -> float:
    # NOT an alias of python.angles.bearing_between_deg on purpose: this module
    # historically wrapped the atan2 angle with plain % 360.0, and the owner's
    # (+360.0) % 360.0 form differs by ~1e-13 deg on positive angles. The local
    # form is kept bit-for-bit (pinned by tests/runtime/core/
    # test_scalar_helper_owners.py).
    return _wrap_deg(math.degrees(math.atan2(float(x1_m) - float(x0_m), float(y1_m) - float(y0_m))))


def _tailwind_component_mps(*, wind_from_deg: float, wind_speed_mps: float, desired_track_deg: float) -> float:
    wind_to_deg = _wrap_deg(float(wind_from_deg) + 180.0)
    rel_rad = math.radians(angle_diff_deg(float(desired_track_deg), wind_to_deg))
    return float(wind_speed_mps) * math.cos(rel_rad)


def turn_rate_limit_deg_s(*, ground_speed_mps: float, bank_limit_deg: float) -> float:
    speed = max(1.0, float(ground_speed_mps))
    bank_rad = math.radians(max(0.0, min(89.0, float(bank_limit_deg))))
    rate_rad_s = 9.80665 * math.tan(bank_rad) / speed
    return abs(math.degrees(rate_rad_s))


@dataclass(frozen=True)
class RouteWaypoint:
    x_m: float
    y_m: float
    altitude_m: float
    speed_mps: float
    radius_m: float
    waypoint_mode: str = "flyby"

    @staticmethod
    def from_mapping(raw: Mapping[str, object] | None, *, default_speed_mps: float = 0.0) -> "RouteWaypoint":
        data = dict(raw or {})
        return RouteWaypoint(
            x_m=float(data.get("x", 0.0)),
            y_m=float(data.get("y", 0.0)),
            altitude_m=float(data.get("altitude_m", data.get("altitude", 0.0))),
            speed_mps=float(data.get("speed_mps", data.get("speed", data.get("target_speed", default_speed_mps)))),
            radius_m=float(data.get("radius_m", 250.0)),
            waypoint_mode=str(data.get("waypoint_mode", "flyby")),
        )


@dataclass(frozen=True)
class RouteSnapshot:
    sim_time_s: float
    x_m: float
    y_m: float
    altitude_m: float
    heading_deg: float
    ground_track_deg: float
    ground_speed_mps: float
    vertical_speed_mps: float
    wind_speed_mps: float
    wind_from_deg: float
    target_heading_deg: float
    target_altitude_m: float
    target_speed_mps: float
    lnav_bank_limit_deg: float
    command_code: int
    waypoint_idx: int


@dataclass(frozen=True)
class CoarseRouteConfig:
    internal_dt_s: float = 0.5
    track_response_s: float = 5.0
    speed_time_constant_s: float = 7.0
    altitude_response_s: float = 24.0
    vertical_speed_time_constant_s: float = 4.0
    climb_rate_limit_mps: float = 35.0
    descent_rate_limit_mps: float = 28.0
    min_ground_speed_mps: float = 55.0
    min_waypoint_capture_radius_m: float = 180.0


@dataclass(frozen=True)
class CoarseRouteForecast:
    horizon_s: float
    state: RouteSnapshot
    waypoint_advances: int
    route_complete: bool


@dataclass(frozen=True)
class RouteErrorMetrics:
    position_error_m: float
    altitude_error_m: float
    ground_speed_error_mps: float
    track_error_deg: float
    waypoint_idx_error: int
    waypoint_mismatch: bool


def project_route_window(
    snapshot: RouteSnapshot,
    *,
    waypoints: Sequence[RouteWaypoint | Mapping[str, object]],
    horizon_s: float,
    config: CoarseRouteConfig | None = None,
) -> CoarseRouteForecast:
    cfg = config or CoarseRouteConfig()
    horizon = max(0.0, float(horizon_s))
    if horizon <= 0.0:
        return CoarseRouteForecast(horizon_s=0.0, state=snapshot, waypoint_advances=0, route_complete=False)

    route = [
        wp if isinstance(wp, RouteWaypoint) else RouteWaypoint.from_mapping(wp, default_speed_mps=float(snapshot.target_speed_mps))
        for wp in list(waypoints or [])
    ]

    x_m = float(snapshot.x_m)
    y_m = float(snapshot.y_m)
    alt_m = float(snapshot.altitude_m)
    heading_deg = _wrap_deg(float(snapshot.heading_deg))
    track_deg = _wrap_deg(float(snapshot.ground_track_deg))
    gs_mps = max(float(cfg.min_ground_speed_mps), float(snapshot.ground_speed_mps))
    vvi_mps = float(snapshot.vertical_speed_mps)
    waypoint_idx = max(0, int(snapshot.waypoint_idx))
    advances = 0

    sim_time_s = float(snapshot.sim_time_s)
    remaining_s = horizon
    internal_dt_s = max(0.1, float(cfg.internal_dt_s))

    while remaining_s > 1.0e-9:
        dt_s = min(remaining_s, internal_dt_s)
        active_wp = route[waypoint_idx] if 0 <= waypoint_idx < len(route) else None
        target_heading_deg = float(snapshot.target_heading_deg)
        target_altitude_m = float(snapshot.target_altitude_m)
        target_speed_mps = float(snapshot.target_speed_mps)

        if active_wp is not None:
            target_heading_deg = bearing_deg(x_m, y_m, active_wp.x_m, active_wp.y_m)
            target_altitude_m = float(active_wp.altitude_m)
            target_speed_mps = float(active_wp.speed_mps)

        target_heading_deg = _wrap_deg(float(target_heading_deg))
        track_err_deg = angle_diff_deg(target_heading_deg, track_deg)
        max_turn_rate_deg_s = turn_rate_limit_deg_s(
            ground_speed_mps=max(gs_mps, float(cfg.min_ground_speed_mps)),
            bank_limit_deg=max(10.0, float(snapshot.lnav_bank_limit_deg)),
        )
        desired_turn_rate_deg_s = float(track_err_deg) / max(0.5, float(cfg.track_response_s))
        applied_turn_rate_deg_s = max(-max_turn_rate_deg_s, min(max_turn_rate_deg_s, desired_turn_rate_deg_s))
        track_deg = _wrap_deg(track_deg + applied_turn_rate_deg_s * dt_s)

        tailwind_mps = _tailwind_component_mps(
            wind_from_deg=float(snapshot.wind_from_deg),
            wind_speed_mps=float(snapshot.wind_speed_mps),
            desired_track_deg=track_deg,
        )
        target_ground_speed_mps = max(float(cfg.min_ground_speed_mps), float(target_speed_mps) + tailwind_mps)
        speed_alpha = 1.0 - math.exp(-dt_s / max(0.5, float(cfg.speed_time_constant_s)))
        gs_mps += (target_ground_speed_mps - gs_mps) * speed_alpha
        gs_mps = max(float(cfg.min_ground_speed_mps), gs_mps)

        desired_vvi_mps = (float(target_altitude_m) - alt_m) / max(1.0, float(cfg.altitude_response_s))
        desired_vvi_mps = max(-float(cfg.descent_rate_limit_mps), min(float(cfg.climb_rate_limit_mps), desired_vvi_mps))
        vvi_alpha = 1.0 - math.exp(-dt_s / max(0.25, float(cfg.vertical_speed_time_constant_s)))
        vvi_mps += (desired_vvi_mps - vvi_mps) * vvi_alpha
        vvi_mps = max(-float(cfg.descent_rate_limit_mps), min(float(cfg.climb_rate_limit_mps), vvi_mps))
        alt_m += vvi_mps * dt_s

        track_rad = math.radians(track_deg)
        x_m += gs_mps * math.sin(track_rad) * dt_s
        y_m += gs_mps * math.cos(track_rad) * dt_s
        heading_deg = track_deg
        sim_time_s += dt_s
        remaining_s -= dt_s

        while 0 <= waypoint_idx < len(route):
            wp = route[waypoint_idx]
            capture_radius_m = max(float(cfg.min_waypoint_capture_radius_m), float(wp.radius_m))
            if distance_m(x_m, y_m, wp.x_m, wp.y_m) > capture_radius_m:
                break
            waypoint_idx += 1
            advances += 1

    final_snapshot = RouteSnapshot(
        sim_time_s=float(sim_time_s),
        x_m=float(x_m),
        y_m=float(y_m),
        altitude_m=float(alt_m),
        heading_deg=float(heading_deg),
        ground_track_deg=float(track_deg),
        ground_speed_mps=float(gs_mps),
        vertical_speed_mps=float(vvi_mps),
        wind_speed_mps=float(snapshot.wind_speed_mps),
        wind_from_deg=float(snapshot.wind_from_deg),
        target_heading_deg=float(snapshot.target_heading_deg),
        target_altitude_m=float(snapshot.target_altitude_m),
        target_speed_mps=float(snapshot.target_speed_mps),
        lnav_bank_limit_deg=float(snapshot.lnav_bank_limit_deg),
        command_code=int(snapshot.command_code),
        waypoint_idx=int(waypoint_idx),
    )
    return CoarseRouteForecast(
        horizon_s=float(horizon),
        state=final_snapshot,
        waypoint_advances=int(advances),
        route_complete=bool(waypoint_idx >= len(route)),
    )


def compare_route_states(predicted: RouteSnapshot, actual: RouteSnapshot) -> RouteErrorMetrics:
    return RouteErrorMetrics(
        position_error_m=float(distance_m(predicted.x_m, predicted.y_m, actual.x_m, actual.y_m)),
        altitude_error_m=float(abs(float(predicted.altitude_m) - float(actual.altitude_m))),
        ground_speed_error_mps=float(abs(float(predicted.ground_speed_mps) - float(actual.ground_speed_mps))),
        track_error_deg=float(abs(angle_diff_deg(float(predicted.ground_track_deg), float(actual.ground_track_deg)))),
        waypoint_idx_error=int(int(predicted.waypoint_idx) - int(actual.waypoint_idx)),
        waypoint_mismatch=bool(int(predicted.waypoint_idx) != int(actual.waypoint_idx)),
    )


def route_waypoints_from_iterable(
    items: Iterable[RouteWaypoint | Mapping[str, object]],
    *,
    default_speed_mps: float = 0.0,
) -> list[RouteWaypoint]:
    out: list[RouteWaypoint] = []
    for item in items:
        if isinstance(item, RouteWaypoint):
            out.append(item)
        else:
            out.append(RouteWaypoint.from_mapping(item, default_speed_mps=float(default_speed_mps)))
    return out
