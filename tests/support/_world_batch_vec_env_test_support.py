from __future__ import annotations


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
