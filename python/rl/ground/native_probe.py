"""Deterministic native Ground training probe.

This adapter deliberately stops at the maintained single-soldier kernel
surface.  It is useful for reset/step/trace/replay checks, but it is not a
production ``WorldBatch`` environment and it exposes no learned or automatic
weapon-employment action.  Its waypoint sequence is a fixed list of direct
targets, not a route graph or path planner.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

import ef_py  # noqa: E402

from .command import build_ground_infantry_mission_command
from .infantry_proxy import GroundInfantryProxyError, normalize_ground_infantry_action


NATIVE_GROUND_PROBE_CONTRACT_VERSION = "ground_infantry_native_probe.v1"


class GroundInfantryNativeProbeError(ValueError):
    """Raised when the native probe cannot represent or execute an action."""


@dataclass(frozen=True)
class NativeGroundInfantryTransition:
    observation: dict[str, tuple[float, ...]]
    reward: float
    terminated: bool
    truncated: bool
    blocked: bool
    blocked_reason: str | None
    truncation_reason: str | None
    trace: dict[str, Any]


@dataclass(frozen=True)
class NativeGroundFireResult:
    """One explicitly authorized fixed-contact fire attempt."""

    success: bool
    target_entity_id: int
    target_damage_before: tuple[float, ...]
    target_damage_after: tuple[float, ...]
    trace: dict[str, Any]


@dataclass(frozen=True)
class NativeGroundRouteValidation:
    """Read-only validation of a configured direct waypoint polyline.

    This is deliberately a sequence validator, not a route graph or planner.
    Each segment is backed by the native transition owner and retains the raw
    seven-field transition observation for replay and diagnosis.
    """

    passable: bool
    segment_count: int
    total_distance_m: float
    blocked_segment_index: int | None
    blocked_reason: str | None
    segment_observations: tuple[tuple[float, ...], ...]
    segment_movement_observations: tuple[tuple[float, ...], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passable": self.passable,
            "segment_count": self.segment_count,
            "total_distance_m": self.total_distance_m,
            "blocked_segment_index": self.blocked_segment_index,
            "blocked_reason": self.blocked_reason,
            "segment_observations": [list(observation) for observation in self.segment_observations],
            "segment_movement_observations": [
                list(observation) for observation in self.segment_movement_observations
            ],
            "authority": "native_probe_only",
            "route_boundary": "fixed_direct_sequence_validation",
        }


class GroundInfantryNativeProbe:
    """Single-soldier reset/step/replay probe backed by ``ef_py.SimulationKernel``."""

    def __init__(
        self,
        *,
        database_dir: str | Path,
        bundle_dir: str | Path,
        overlay_path: str | Path | None = None,
        start_xy_m: tuple[float, float] = (400.0, 100.0),
        goal_xy_m: tuple[float, float] = (600.0, 100.0),
        waypoints_xy_m: Sequence[Sequence[float]] | None = None,
        goal_radius_m: float = 5.0,
        max_speed_mps: float = 1.5,
        max_steps: int = 256,
        blocked_step_limit: int = 8,
        time_step_s: float = 1.0 / 60.0,
        target_xy_m: tuple[float, float] | None = None,
    ) -> None:
        self.database_dir = Path(database_dir)
        self.bundle_dir = Path(bundle_dir)
        self.overlay_path = Path(overlay_path) if overlay_path is not None else None
        self.start_xy_m = (float(start_xy_m[0]), float(start_xy_m[1]))
        raw_waypoints = (goal_xy_m,) if waypoints_xy_m is None else tuple(waypoints_xy_m)
        if not raw_waypoints:
            raise ValueError("waypoints_xy_m must contain at least one waypoint")
        normalized_waypoints: list[tuple[float, float]] = []
        for waypoint in raw_waypoints:
            if len(waypoint) != 2:
                raise ValueError("each waypoint must contain exactly two coordinates")
            x, y = float(waypoint[0]), float(waypoint[1])
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError("waypoint coordinates must be finite")
            normalized_waypoints.append((x, y))
        self.waypoints_xy_m = tuple(normalized_waypoints)
        self._waypoint_index = 0
        self.goal_xy_m = self.waypoints_xy_m[0]
        self.goal_radius_m = float(goal_radius_m)
        self.max_speed_mps = float(max_speed_mps)
        self.max_steps = int(max_steps)
        self.blocked_step_limit = int(blocked_step_limit)
        self.time_step_s = float(time_step_s)
        if target_xy_m is not None and len(target_xy_m) != 2:
            raise ValueError("target_xy_m must contain exactly two coordinates")
        self.target_xy_m = (
            None
            if target_xy_m is None
            else (float(target_xy_m[0]), float(target_xy_m[1]))
        )
        if self.target_xy_m is not None and not all(
            math.isfinite(value) for value in self.target_xy_m
        ):
            raise ValueError("target_xy_m must contain finite coordinates")
        if self.goal_radius_m <= 0.0 or self.max_speed_mps <= 0.0:
            raise ValueError("goal_radius_m and max_speed_mps must be positive")
        if self.max_steps <= 0 or self.blocked_step_limit <= 0 or self.time_step_s <= 0.0:
            raise ValueError("max_steps, blocked_step_limit, and time_step_s must be positive")
        self._sim: Any | None = None
        self._entity_id: int | None = None
        self._step_index = 0
        self._blocked_steps = 0
        self._stance = "stand"
        self._target_entity_id: int | None = None

    @classmethod
    def from_fixture(cls, fixture_dir: str | Path | None = None, **kwargs: Any) -> "GroundInfantryNativeProbe":
        root = Path(__file__).resolve().parents[3]
        fixture = Path(fixture_dir) if fixture_dir is not None else (
            root
            / "tests"
            / "scenario"
            / "fixtures"
            / "environment_substrate"
            / "arnis_bundle_v1"
            / "eastern_plain_infantry_phase1"
        )
        return cls(
            database_dir=root / "examples" / "config" / "database",
            bundle_dir=fixture / "expected",
            overlay_path=fixture / "field_overlay.json",
            **kwargs,
        )

    def _require_ready(self) -> tuple[Any, int]:
        if self._sim is None or self._entity_id is None:
            raise RuntimeError("GroundInfantryNativeProbe.reset must be called first")
        return self._sim, self._entity_id

    @staticmethod
    def _tuple(values: Sequence[Any]) -> tuple[float, ...]:
        return tuple(float(value) for value in values)

    def _observation(self) -> dict[str, tuple[float, ...]]:
        sim, entity_id = self._require_ready()
        position = self._tuple(sim.get_unit_position(entity_id))
        velocity = self._tuple(sim.get_unit_velocity(entity_id))
        terrain = self._tuple(sim.get_ground_terrain_observation(position[0], position[1]))
        slope_deg = float(sim.get_ground_slope_deg(position[0], position[1]))
        movement_effects = self._tuple(
            sim.get_ground_movement_effect_observation(
                position[0],
                position[1],
                ("stand", "crouch", "prone").index(self._stance),
            )
        )
        semantic = self._tuple(
            sim.get_ground_field_semantic_observation(position[0], position[1])
        )
        weapon = self._tuple(sim.get_ground_weapon_state(entity_id))
        health = self._tuple(sim.get_unit_health(entity_id))
        command = sim.get_mission_command(entity_id)
        goal_dx = self.goal_xy_m[0] - position[0]
        goal_dy = self.goal_xy_m[1] - position[1]
        goal_distance = math.hypot(goal_dx, goal_dy)
        return {
            "position_local_enu_m": position,
            "velocity_local_enu_mps": velocity,
            "terrain": terrain,
            "terrain_effects": (slope_deg,),
            "movement_effects": movement_effects,
            "field_semantics": semantic,
            "weapon_state": weapon,
            "health_state": health,
            "command_state": (
                1.0 if bool(command.active) else 0.0,
                float(command.cmd_heading_deg),
                float(command.cmd_speed_mps),
                float(int(command.ground_task_mode)),
                float(int(command.ground_stance)),
                float(command.objective_area_id),
                float(command.objective_node_id),
            ),
            "mission_state": (goal_dx, goal_dy, goal_distance),
            "waypoint_state": (
                float(self._waypoint_index),
                float(len(self.waypoints_xy_m)),
            ),
            "state": (
                float(sim.get_unit_heading(entity_id)),
                float(("stand", "crouch", "prone").index(self._stance)),
                float(self._step_index),
            ),
        }

    def validate_waypoint_sequence(self) -> NativeGroundRouteValidation:
        """Validate the configured direct waypoint polyline without mutating state."""

        sim, _entity_id = self._require_ready()
        points = (self.start_xy_m,) + self.waypoints_xy_m
        observations: list[tuple[float, ...]] = []
        movement_observations: list[tuple[float, ...]] = []
        total_distance = 0.0
        blocked_segment_index: int | None = None
        blocked_reason: str | None = None
        for segment_index, (start, end) in enumerate(zip(points, points[1:])):
            transition = self._tuple(
                sim.get_ground_transition_observation(
                    start[0], start[1], end[0], end[1]
                )
            )
            if len(transition) != 7:
                raise GroundInfantryNativeProbeError(
                    "native route validation expected seven transition fields"
                )
            movement = self._tuple(
                sim.get_ground_transition_movement_observation(
                    start[0],
                    start[1],
                    end[0],
                    end[1],
                    ("stand", "crouch", "prone").index(self._stance),
                )
            )
            if len(movement) != 10:
                raise GroundInfantryNativeProbeError(
                    "native route validation expected ten movement fields"
                )
            observations.append(transition)
            movement_observations.append(movement)
            total_distance += math.hypot(end[0] - start[0], end[1] - start[1])
            if transition[1] > 0.5 or blocked_segment_index is not None:
                continue
            blocked_segment_index = segment_index
            if transition[3] > 0.5:
                blocked_reason = "water_transition_blocked"
            elif transition[4] > 0.5:
                blocked_reason = "obstacle_transition_blocked"
            elif transition[0] <= 0.5:
                blocked_reason = "unconfigured_transition"
            else:
                blocked_reason = "destination_terrain_blocked"
        return NativeGroundRouteValidation(
            passable=blocked_segment_index is None,
            segment_count=len(observations),
            total_distance_m=total_distance,
            blocked_segment_index=blocked_segment_index,
            blocked_reason=blocked_reason,
            segment_observations=tuple(observations),
            segment_movement_observations=tuple(movement_observations),
        )

    def fire_from_mission_command(self) -> NativeGroundFireResult:
        """Fire once at the optional fixed contact through the native command gate."""

        sim, entity_id = self._require_ready()
        if self._target_entity_id is None:
            raise GroundInfantryNativeProbeError(
                "native fire probe requires target_xy_m at construction"
            )
        target_id = self._target_entity_id
        before = self._tuple(sim.get_unit_damage_state(target_id))
        weapon_before = self._tuple(sim.get_ground_weapon_state(entity_id))
        command = ef_py.MissionCommand()
        command.active = True
        command.ground_task_mode = ef_py.GroundTaskMode.OccupyStatic
        command.assigned_target_id = target_id
        command.engagement_authority_holder_id = entity_id
        command.authorization_to_fire = True
        sim.set_mission_command(entity_id, command)
        success = bool(sim.fire_ground_weapon_from_mission_command(entity_id))
        after = self._tuple(sim.get_unit_damage_state(target_id))
        weapon_after = self._tuple(sim.get_ground_weapon_state(entity_id))
        trace = {
            "contract_version": NATIVE_GROUND_PROBE_CONTRACT_VERSION,
            "authority": "native_probe_only",
            "event": "fire_from_mission_command",
            "success": success,
            "attacker_entity_id": entity_id,
            "target_entity_id": target_id,
            "target_damage_before": before,
            "target_damage_after": after,
            "weapon_before": weapon_before,
            "weapon_after": weapon_after,
            "requires": ["terrain_line_of_sight"],
            "does_not_claim": [
                "target_selection",
                "cover",
                "concealment",
                "suppression",
                "ballistics",
            ],
        }
        return NativeGroundFireResult(
            success=success,
            target_entity_id=target_id,
            target_damage_before=before,
            target_damage_after=after,
            trace=trace,
        )

    def replay(
        self,
        actions: Sequence[Mapping[str, Any] | Sequence[float]],
        *,
        seed: int = 42,
    ) -> tuple[dict[str, Any], ...]:
        """Reset and replay a bounded direct-action sequence without live providers."""

        _observation, info = self.reset(seed=seed)
        records: list[dict[str, Any]] = [info["trace"]]
        for action in actions:
            transition = self.step(action)
            records.append(transition.trace)
            if transition.terminated or transition.truncated:
                break
        return tuple(records)

    def reset(self, *, seed: int = 42) -> tuple[dict[str, tuple[float, ...]], dict[str, Any]]:
        sim = ef_py.SimulationKernel()
        if not sim.load_database(str(self.database_dir)):
            raise GroundInfantryNativeProbeError("native probe database load failed")
        sim.set_time_step(self.time_step_s)
        if not sim.load_arnis_terrain_bundle(str(self.bundle_dir)):
            raise GroundInfantryNativeProbeError("native probe Arnis bundle load failed")
        if self.overlay_path is not None and not sim.load_arnis_field_overlay(str(self.overlay_path)):
            raise GroundInfantryNativeProbeError("native probe field overlay load failed")
        sim.reset(int(seed))
        entity_id = int(
            sim.spawn_unit(
                ef_py.Side.Blue,
                "Ground_Infantry_Soldier_MVP",
                self.start_xy_m[0],
                self.start_xy_m[1],
                0.0,
            )
        )
        if entity_id <= 0:
            raise GroundInfantryNativeProbeError("native probe infantry spawn failed")
        self._target_entity_id = None
        if self.target_xy_m is not None:
            target_id = int(
                sim.spawn_unit(
                    ef_py.Side.Red,
                    "Ground_Infantry_Soldier_MVP",
                    self.target_xy_m[0],
                    self.target_xy_m[1],
                    0.0,
                )
            )
            if target_id <= 0:
                raise GroundInfantryNativeProbeError("native probe target spawn failed")
            target_dx = self.target_xy_m[0] - self.start_xy_m[0]
            target_dy = self.target_xy_m[1] - self.start_xy_m[1]
            track = ef_py.Detection()
            track.target_id = target_id
            track.range = math.hypot(target_dx, target_dy)
            track.bearing = math.degrees(math.atan2(target_dx, target_dy))
            track.elevation = 0.0
            track.closing_speed = 0.0
            track.signal_strength = 1.0
            track.snr_db = 20.0
            track.detection_prob_used = 1.0
            track.measured_vr = 0.0
            track.sensor_type = int(ef_py.SensorType.Visual)
            track.local_sensor_hit = True
            track.timestamp = 0.0
            sim.set_contact_list(entity_id, [track])
            self._target_entity_id = target_id
        sim.set_command_link(entity_id, 0.0, 0.0)
        self._sim = sim
        self._entity_id = entity_id
        self._step_index = 0
        self._blocked_steps = 0
        self._stance = "stand"
        self._waypoint_index = 0
        self.goal_xy_m = self.waypoints_xy_m[0]
        observation = self._observation()
        route_validation = self.validate_waypoint_sequence()
        return observation, {
            "contract_version": NATIVE_GROUND_PROBE_CONTRACT_VERSION,
            "authority": "native_probe_only",
            "production_boundary": "not_world_batch",
            "seed": int(seed),
            "entity_id": entity_id,
            "goal_xy_m": self.goal_xy_m,
            "waypoint_index": self._waypoint_index,
            "waypoint_count": len(self.waypoints_xy_m),
            "route_validation": route_validation.as_dict(),
            "trace": {
                "event": "reset",
                "seed": int(seed),
                "observation": observation,
                "waypoint_index": self._waypoint_index,
                "waypoint_count": len(self.waypoints_xy_m),
                "route_validation": route_validation.as_dict(),
            },
        }

    def step(
        self, action: Mapping[str, Any] | Sequence[float]
    ) -> NativeGroundInfantryTransition:
        sim, entity_id = self._require_ready()
        try:
            normalized = normalize_ground_infantry_action(action)
            command = build_ground_infantry_mission_command(
                normalized, max_speed_mps=self.max_speed_mps
            )
        except (GroundInfantryProxyError, ValueError, TypeError) as exc:
            raise GroundInfantryNativeProbeError(str(exc)) from exc
        before = self._observation()
        waypoint_index_before = self._waypoint_index
        previous_distance = math.hypot(
            self.goal_xy_m[0] - before["position_local_enu_m"][0],
            self.goal_xy_m[1] - before["position_local_enu_m"][1],
        )
        self._stance = normalized.stance
        sim.set_mission_command(entity_id, command)
        sim.step()
        self._step_index += 1
        after = self._observation()
        heading_rad = math.radians(normalized.desired_heading_deg)
        commanded_distance = (
            normalized.desired_speed_fraction * self.max_speed_mps * self.time_step_s
        )
        start_effects = self._tuple(
            sim.get_ground_movement_effect_observation(
                before["position_local_enu_m"][0],
                before["position_local_enu_m"][1],
                ("stand", "crouch", "prone").index(normalized.stance),
            )
        )
        effective_distance = commanded_distance * max(0.0, start_effects[7])
        transition_observation = self._tuple(
            sim.get_ground_transition_observation(
                before["position_local_enu_m"][0],
                before["position_local_enu_m"][1],
                before["position_local_enu_m"][0] + math.sin(heading_rad) * commanded_distance,
                before["position_local_enu_m"][1] + math.cos(heading_rad) * commanded_distance,
            )
        )
        transition_effects = self._tuple(
            sim.get_ground_transition_movement_observation(
                before["position_local_enu_m"][0],
                before["position_local_enu_m"][1],
                before["position_local_enu_m"][0] + math.sin(heading_rad) * effective_distance,
                before["position_local_enu_m"][1] + math.cos(heading_rad) * effective_distance,
                ("stand", "crouch", "prone").index(normalized.stance),
            )
        )
        moved_distance = math.hypot(
            after["position_local_enu_m"][0] - before["position_local_enu_m"][0],
            after["position_local_enu_m"][1] - before["position_local_enu_m"][1],
        )
        requested_motion = normalized.desired_speed_fraction > 0.0
        blocked = requested_motion and moved_distance <= 1.0e-12
        current_surface = int(round(before["terrain"][1]))
        transition_water_blocked = transition_observation[3] > 0.5
        transition_obstacle_blocked = transition_observation[4] > 0.5
        blocked_reason = None
        if blocked:
            if transition_water_blocked:
                blocked_reason = "water_transition_blocked"
            elif transition_obstacle_blocked:
                blocked_reason = "obstacle_transition_blocked"
            elif current_surface in (4, 5):
                blocked_reason = "current_terrain_blocked"
            else:
                blocked_reason = "destination_terrain_blocked"
            self._blocked_steps += 1
        else:
            self._blocked_steps = 0
        current_distance = math.hypot(
            self.goal_xy_m[0] - after["position_local_enu_m"][0],
            self.goal_xy_m[1] - after["position_local_enu_m"][1],
        )
        reward = float(previous_distance - current_distance) - (0.1 if blocked else 0.0)
        waypoint_reached = current_distance <= self.goal_radius_m
        incapacitated = after["health_state"][0] <= 0.0
        waypoint_advanced = False
        if (
            waypoint_reached
            and not incapacitated
            and self._waypoint_index + 1 < len(self.waypoints_xy_m)
        ):
            self._waypoint_index += 1
            self.goal_xy_m = self.waypoints_xy_m[self._waypoint_index]
            waypoint_advanced = True
            after = self._observation()
        final_waypoint_reached = waypoint_reached and not waypoint_advanced
        terminated = final_waypoint_reached or incapacitated
        termination_reason = (
            "agent_incapacitated"
            if incapacitated
            else "waypoint_reached"
            if final_waypoint_reached
            else None
        )
        truncation_reason = None
        if not terminated and self._blocked_steps >= self.blocked_step_limit:
            truncation_reason = "blocked_step_limit"
        elif not terminated and self._step_index >= self.max_steps:
            truncation_reason = "max_steps"
        truncated = truncation_reason is not None
        trace = {
            "contract_version": NATIVE_GROUND_PROBE_CONTRACT_VERSION,
            "authority": "native_probe_only",
            "step_index": self._step_index,
            "action": list(normalized.vector()),
            "before": before,
            "after": after,
            "transition_observation": transition_observation,
            "transition_effects": transition_effects,
            "start_movement_effects": start_effects,
            "requested_distance_m": commanded_distance,
            "effective_probe_distance_m": effective_distance,
            "moved_distance_m": moved_distance,
            "blocked": blocked,
            "blocked_reason": blocked_reason,
            "waypoint_index_before": waypoint_index_before,
            "waypoint_index_after": self._waypoint_index,
            "waypoint_advanced": waypoint_advanced,
            "terminated": terminated,
            "termination_reason": termination_reason,
            "truncated": truncated,
            "truncation_reason": truncation_reason,
        }
        return NativeGroundInfantryTransition(
            observation=after,
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            blocked=blocked,
            blocked_reason=blocked_reason,
            truncation_reason=truncation_reason,
            trace=trace,
        )


__all__ = [
    "GroundInfantryNativeProbe",
    "GroundInfantryNativeProbeError",
    "NativeGroundFireResult",
    "NativeGroundRouteValidation",
    "NATIVE_GROUND_PROBE_CONTRACT_VERSION",
    "NativeGroundInfantryTransition",
]
