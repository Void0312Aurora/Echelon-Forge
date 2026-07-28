from __future__ import annotations

import json

import ef_py


def _inline_vec_env_scenario() -> dict:
  return {
    "scenario_name": "phase4_world_batch_vec_env_inline",
    "meta": {
      "max_steps": 1,
    },
    "environment": {
      "time_step": 0.05,
      "terrain_type": "legacy",
      "wind": {
        "speed_mps": 4.0,
        "dir_from_deg": 180.0,
        "shear_mps_per_km": 0.0,
      },
      "zones": [
        {
          "name": "Runway_A",
          "x": 0.0,
          "y": 0.0,
          "width": 60.0,
          "length": 2500.0,
          "heading": 90.0,
          "surface": "Concrete",
        }
      ],
    },
    "mission_command": {
      "command_code": 2,
      "target_heading": 90.0,
      "target_altitude": 1200.0,
      "target_speed": 180.0,
    },
    "entities": [
      {
        "name": "Lead",
        "type": "Aircraft",
        "side": "Blue",
        "is_agent": True,
        "pos": [-1400.0, 0.0, 1200.0],
        "vel": [0.0, 180.0, 0.0],
        "heading": 90.0,
      }
    ],
  }


def _inline_vec_env_maritime_scenario() -> dict:
  scenario = _inline_vec_env_scenario()
  scenario["environment"]["maritime"] = {
    "sea_state": 0.0,
    "wave_heading_deg": 135.0,
    "wave_period_s": 11.0,
  }
  return scenario


def _legacy_step_result_state_with_poisoned_report_fields(source_state) -> ef_py.ExecutionEpisodeState:
  state = ef_py.ExecutionEpisodeState()
  state.agent_id = int(getattr(source_state, "agent_id", 0))
  state.step_count = int(getattr(source_state, "step_count", 0)) + 100
  state.prev_altitude_m = float(getattr(source_state, "prev_altitude_m", 0.0)) + 250.0
  state.last_termination_reason = "legacy_step_result_reason"
  state.last_reward_total = 91.25
  state.last_reward_breakdown_json = json.dumps(
    {"legacy_total": 91.25, "total": 91.25},
    ensure_ascii=True,
    sort_keys=True,
  )
  return state


def _inline_vec_env_route_transition_scenario() -> dict:
  scenario = _inline_vec_env_scenario()
  scenario["meta"]["max_steps"] = 3
  scenario["mission_command"] = {
    "command_code": 3,
    "target_heading": 90.0,
    "target_altitude": 1200.0,
    "target_speed": 180.0,
    "waypoint_mode": "flyby",
    "waypoints": [
      {"x": -1350.0, "y": 0.0, "z": 1200.0, "radius_m": 1200.0},
    ],
    "post_waypoint_transition": {
      "command_code": 2,
      "target_heading": 45.0,
      "target_altitude": 900.0,
      "target_speed": 160.0,
      "phase_name": "post_route",
      "transition_reward": 123.0,
    },
  }
  return scenario


def _inline_air_combat_scripted_opponent_scenario() -> dict:
  return {
    "scenario_name": "air_combat_world_batch_scripted_opponent_inline",
    "environment": {
      "time_step": 0.05,
      "max_steps": 320,
      "terrain_type": "flat",
      "wind": {
        "speed_mps": 0.0,
        "dir_from_deg": 0.0,
        "shear_mps_per_km": 0.0,
      },
    },
    "mission_command": {
      "command_code": 0,
      "target_heading": 0.0,
      "target_altitude": 1200.0,
      "target_speed": 180.0,
      "assigned_target_name": "Red_Fighter",
      "authorization_to_fire": True,
    },
    "entities": [
      {
        "name": "Blue_Fighter",
        "type": "F-16C_Block50",
        "side": "Blue",
        "is_agent": True,
        "pos": [0.0, 0.0, 1200.0],
        "vel": [0.0, 180.0, 0.0],
        "heading": 0.0,
        "ammo": {
          "missiles_remaining": 4,
          "max_missiles": 4,
        },
        "weapon_cooldown": {
          "cooldown_s": 0.75,
          "last_fire_time": -1.0,
        },
      },
      {
        "name": "Red_Fighter",
        "type": "F-16C_Block50",
        "side": "Red",
        "pos": [0.0, 8000.0, 1200.0],
        "vel": [0.0, -180.0, 0.0],
        "heading": 180.0,
        "scripted_agent": {
          "name": "red_scripted_agent",
          "target_name": "Blue_Fighter",
          "fire_range_m": 9000.0,
          "threat_range_m": 9000.0,
          "merge_range_m": 3500.0,
        },
        "ammo": {
          "missiles_remaining": 4,
          "max_missiles": 4,
        },
        "weapon_cooldown": {
          "cooldown_s": 0.75,
          "last_fire_time": -1.0,
        },
      },
    ],
  }


def _controller_runtime_state_matches_loader_state(runtime_state, loader_state) -> bool:
  def _canonicalize_json(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
      return str(raw or "")
    try:
      parsed = json.loads(raw)
    except Exception:
      return str(raw)

    def _strip_internal_fields(value):
      if isinstance(value, dict):
        return {
          str(key): _strip_internal_fields(item)
          for key, item in value.items()
          if not str(key).startswith("_")
        }
      if isinstance(value, list):
        return [_strip_internal_fields(item) for item in value]
      return value

    return json.dumps(_strip_internal_fields(parsed), ensure_ascii=True, sort_keys=True)

  def _route_digest(state) -> list[tuple[float, float, float, float, float, float, str]]:
    route = []
    for waypoint in list(getattr(state, "route_waypoints", [])):
      route.append(
        (
          float(getattr(waypoint, "x_m", 0.0)),
          float(getattr(waypoint, "y_m", 0.0)),
          float(getattr(waypoint, "z_m", 0.0)),
          float(getattr(waypoint, "radius_m", 0.0)),
          float(getattr(waypoint, "altitude_m", 0.0)),
          float(getattr(waypoint, "speed_mps", 0.0)),
          str(getattr(waypoint, "waypoint_mode", "")),
        )
      )
    return route

  runtime_digest = {
    "has_mission_command_json": bool(getattr(runtime_state, "has_mission_command_json", False)),
    "mission_command_json": _canonicalize_json(str(getattr(runtime_state, "mission_command_json", ""))),
    "route_waypoints": _route_digest(runtime_state),
    "has_post_waypoint_transition_json": bool(getattr(runtime_state, "has_post_waypoint_transition_json", False)),
    "post_waypoint_transition_json": _canonicalize_json(str(getattr(runtime_state, "post_waypoint_transition_json", ""))),
    "mission_phase_name": str(getattr(runtime_state, "mission_phase_name", "")),
    "has_cached_route_ref_id": bool(getattr(runtime_state, "has_cached_route_ref_id", False)),
    "cached_route_ref_id": int(getattr(runtime_state, "cached_route_ref_id", 0)),
  }
  loader_digest = {
    "has_mission_command_json": bool(getattr(loader_state, "has_mission_command_json", False)),
    "mission_command_json": _canonicalize_json(str(getattr(loader_state, "mission_command_json", ""))),
    "route_waypoints": _route_digest(loader_state),
    "has_post_waypoint_transition_json": bool(getattr(loader_state, "has_post_waypoint_transition_json", False)),
    "post_waypoint_transition_json": _canonicalize_json(str(getattr(loader_state, "post_waypoint_transition_json", ""))),
    "mission_phase_name": str(getattr(loader_state, "mission_phase_name", "")),
    "has_cached_route_ref_id": bool(getattr(loader_state, "has_cached_route_ref_id", False)),
    "cached_route_ref_id": int(getattr(loader_state, "cached_route_ref_id", 0)),
  }
  return runtime_digest == loader_digest
