from __future__ import annotations

import unittest

import ef_py

def _make_detection(target_id: int, *, range_m: float = 8000.0) -> ef_py.Detection:
  detection = ef_py.Detection()
  detection.target_id = int(target_id)
  detection.range = float(range_m)
  detection.bearing = 0.0
  detection.elevation = 0.0
  detection.closing_speed = 350.0
  detection.signal_strength = 1.0
  detection.detection_prob_used = 1.0
  detection.sensor_type = int(ef_py.SensorType.Radar)
  detection.local_sensor_hit = True
  detection.timestamp = 0.0
  return detection

def _spawn_request(
  *,
  world_index: int,
  type_name: str,
  entity_name: str,
  x: float,
  y: float,
  z: float = 1200.0,
  heading: float = 90.0,
  vy: float = 180.0,
  missiles_remaining: int = 2,
  max_missiles: int = 6,
  weapon_cooldown_s: float = 10.0,
  weapon_last_fire_time: float = 0.0,
) -> ef_py.WorldSpawnRequest:
  request = ef_py.WorldSpawnRequest()
  request.world_index = int(world_index)
  request.side = ef_py.Side.Blue
  request.type_name = type_name
  request.entity_name = entity_name
  request.is_agent = True
  request.x = float(x)
  request.y = float(y)
  request.z = float(z)
  request.heading = float(heading)
  request.vy = float(vy)
  request.ammo_override_enabled = True
  request.missiles_remaining = int(missiles_remaining)
  request.max_missiles = int(max_missiles)
  request.weapon_cooldown_override_enabled = True
  request.weapon_cooldown_s = float(weapon_cooldown_s)
  request.weapon_last_fire_time = float(weapon_last_fire_time)
  return request

def _assert_gpu_helper_capabilities_remain_fail_closed(testcase: unittest.TestCase) -> None:
  capabilities = ef_py.RuntimeFacade(1).capabilities()
  for field in (
    "supports_gpu_visual",
    "supports_gpu_observation",
    "supports_gpu_flight_shaping",
    "supports_device_observation_view",
    "supports_resident_state",
    "supports_exact_gpu_backend",
    "supports_shadow_compare",
  ):
    testcase.assertFalse(
      bool(getattr(capabilities, field)),
      msg=f"{field} must remain false after helper-backed candidate queries",
    )
  testcase.assertEqual(
    str(capabilities.device_observation_view_candidate_profile_id),
    "gpu_helpers.diagnostics_only",
  )
  testcase.assertEqual(
    str(capabilities.device_observation_view_rejection_reason),
    "gpu_helpers_diagnostics_only_is_not_a_maintained_device_observation_view_profile",
  )

def _inline_batch_scenario() -> dict:
  return {
    "scenario_name": "phase4_batch_runtime_inline",
    "environment": {
      "time_step": 0.05,
      "terrain_type": "legacy",
      "wind": {
        "speed_mps": 6.0,
        "dir_from_deg": 210.0,
        "shear_mps_per_km": 0.5,
      },
      "randomization": {
        "world_yaw_range": [-20.0, 20.0],
        "world_yaw_origin": [0.0, 0.0],
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
        "randomization": {
          "along_body_m_range": [-100.0, 100.0],
          "cross_body_m_range": [-50.0, 50.0],
          "heading_offset_deg_range": [-5.0, 5.0],
        },
      },
      {
        "name": "Wing",
        "type": "Aircraft",
        "side": "Blue",
        "is_agent": True,
        "pos": [-1550.0, -120.0, 1200.0],
        "vel": [0.0, 180.0, 0.0],
        "heading": 90.0,
      },
    ],
    "cooperative_roster": {
      "team_id": 7001,
      "element_id": 7001,
      "policy_route": "shared_execution",
      "members": [
        {
          "entity": "Lead",
          "role_code": 21,
          "formation_role_id": "ElementLead",
          "relative_slot_code": 11,
        },
        {
          "entity": "Wing",
          "role_code": 22,
          "formation_role_id": "Wingman",
          "relative_slot_code": 12,
          "reference_entity": "Lead",
        },
      ],
    },
  }

def _inline_route_scenario() -> dict:
  scenario = _inline_batch_scenario()
  scenario["mission_command"] = {
    "command_code": 3,
    "target_heading": 90.0,
    "target_altitude": 1200.0,
    "target_speed": 180.0,
    "waypoint_mode": "flyby",
    "waypoints": [
      {"x": -500.0, "y": 0.0, "z": 1200.0, "radius_m": 800.0},
      {"x": 2500.0, "y": 1500.0, "z": 1200.0, "radius_m": 800.0},
    ],
  }
  return scenario
