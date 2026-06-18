from __future__ import annotations

import unittest
from types import SimpleNamespace

from gym_envs.scenario_loader.reward_runtime.air_combat import (
  apply_air_combat_reward_surface,
  combat_entity_terminal_state,
)


def _loader(rewards: dict) -> SimpleNamespace:
  loader = SimpleNamespace()
  loader.get_rewards_config = lambda: dict(rewards)
  loader.scenario_data = {"realism_gradient": {"domain": "air_combat"}}
  loader._compiled_meta_cfg = {}
  loader._scenario_source_path = "scenarios/air_combat/1v1/test.json"
  loader._air_combat_reward_last_report_id = 0
  loader._air_combat_reward_prev_missiles = 4
  loader._air_combat_reward_release_count = 0
  loader._last_action_mode = "air_combat_hybrid_v1"
  loader._last_effective_action = [0.0, 0.0, 0.0, 0.6, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0]
  loader.agent_id = 1
  loader.primary_target_id = 2
  loader.mission_cmd = {
    "assigned_target_id": 2,
    "authorization_to_fire": True,
    "roe_state": 3,
  }
  return loader


def _sim() -> SimpleNamespace:
  return SimpleNamespace(
    export_recent_engagement_events=lambda: SimpleNamespace(damage_reports=[], effects_events=[]),
  )


def _entity_ref(entity_id: int) -> SimpleNamespace:
  return SimpleNamespace(entity_id=int(entity_id), world_index=int(entity_id))


def _lethality_header(
  event_id: int,
  target_id: int,
  *,
  consumer_visibility: str = "diagnostics_and_training",
) -> SimpleNamespace:
  return SimpleNamespace(
    event_id=int(event_id),
    target=_entity_ref(target_id),
    consumer_visibility=str(consumer_visibility),
  )


def _damage_report(
  *,
  report_id: int = 7,
  target_id: int = 2,
  platform_damage_state_delta: str = "mission=-0.200000,mobility=-0.300000,sensor=0.000000,survivability=-0.500000",
) -> SimpleNamespace:
  return SimpleNamespace(
    report_id=int(report_id),
    target=_entity_ref(target_id),
    system_health_delta=-0.5,
    platform_damage_state_delta=str(platform_damage_state_delta),
    mission_kill=True,
    mobility_kill=False,
    sensor_kill=False,
    survivability_kill=True,
    loss_state_from="combat_capable",
    loss_state_to="lost",
    destroyed=True,
  )


def _platform_consequence_event(
  *,
  event_id: int = 7,
  target_id: int = 2,
  consumer_visibility: str = "diagnostics_and_training",
) -> SimpleNamespace:
  return SimpleNamespace(
    header=_lethality_header(
      event_id,
      target_id,
      consumer_visibility=consumer_visibility,
    ),
    mission_capability_before=1.0,
    mission_capability_after=0.8,
    mobility_capability_before=1.0,
    mobility_capability_after=0.7,
    sensor_capability_before=1.0,
    sensor_capability_after=1.0,
    survivability_capability_before=1.0,
    survivability_capability_after=0.5,
    mission_kill=True,
    mobility_kill=False,
    sensor_kill=False,
    survivability_kill=True,
  )


def _lifecycle_transition_event(
  *,
  event_id: int = 8,
  target_id: int = 2,
  lifecycle_to: str = "lost",
  ground_lifecycle: str = "unknown",
  terminal: bool = True,
) -> SimpleNamespace:
  return SimpleNamespace(
    header=_lethality_header(event_id, target_id),
    lifecycle_from="combat_capable",
    lifecycle_to=str(lifecycle_to),
    ground_lifecycle=str(ground_lifecycle),
    terminal=bool(terminal),
  )


def _event_sim(
  *,
  damage_reports: list[SimpleNamespace] | None = None,
  platform_consequence_events: list[SimpleNamespace] | None = None,
  lifecycle_transition_events: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
  events = SimpleNamespace(
    damage_reports=list(damage_reports or []),
    effects_events=[],
    platform_consequence_events=list(platform_consequence_events or []),
    lifecycle_transition_events=list(lifecycle_transition_events or []),
  )
  return SimpleNamespace(
    export_recent_engagement_events=lambda: events,
    is_unit_active=lambda entity_id: True,
  )


_AIRCRAFT_DAMAGE_STATE_FIELDS = (
  "structural_integrity",
  "flight_control_integrity",
  "hydraulic_integrity",
  "hydraulic_pressure_availability",
  "roll_control_integrity",
  "pitch_control_integrity",
  "yaw_control_integrity",
  "control_asymmetry",
  "propulsion_integrity",
  "fuel_system_integrity",
  "avionics_integrity",
  "crew_effectiveness",
  "pilot_effectiveness",
  "mission_crew_effectiveness",
  "command_navigation_integrity",
  "fire_severity",
  "fuel_leak_severity",
  "fuel_imbalance_severity",
  "flammable_fluid_exposure",
  "ignition_source_severity",
  "fire_suppression_integrity",
  "smoke_heat_exposure",
  "engine_fire_zone_severity",
  "wing_fire_zone_severity",
  "fuselage_fire_zone_severity",
  "mission_fire_zone_severity",
  "structural_overstress",
  "flutter_exposure",
  "forced_landing_required",
  "flight_control_kill",
  "propulsion_kill",
  "crew_kill",
)
_GROUND_CONTACT_STATE_FIELDS = (
  "on_ground",
  "terrain_z",
  "lifecycle",
  "impact_h_speed",
  "impact_sink_rate",
  "impact_severity",
  "gear_stress",
  "gear_collapsed",
  "on_runway",
)


def _aircraft_damage_state(**overrides: float) -> list[float]:
  values: dict[str, float] = {}
  for field in _AIRCRAFT_DAMAGE_STATE_FIELDS:
    if (
      field.endswith("_integrity")
      or field.endswith("_availability")
      or field.endswith("_effectiveness")
    ):
      values[field] = 1.0
    else:
      values[field] = 0.0
  values.update({str(key): float(value) for key, value in overrides.items()})
  return [float(values[field]) for field in _AIRCRAFT_DAMAGE_STATE_FIELDS]


def _ground_contact_state(**overrides: float) -> list[float]:
  values = {
    "on_ground": 0.0,
    "terrain_z": 0.0,
    "lifecycle": 0.0,
    "impact_h_speed": 0.0,
    "impact_sink_rate": 0.0,
    "impact_severity": 0.0,
    "gear_stress": 0.0,
    "gear_collapsed": 0.0,
    "on_runway": 1.0,
  }
  values.update({str(key): float(value) for key, value in overrides.items()})
  return [float(values[field]) for field in _GROUND_CONTACT_STATE_FIELDS]


def _consequence_sim(
  *,
  aircraft: dict[int, list[float]] | None = None,
  ground: dict[int, list[float]] | None = None,
) -> SimpleNamespace:
  sim = SimpleNamespace()
  sim.aircraft = dict(aircraft or {})
  sim.ground = dict(ground or {})
  sim.export_recent_engagement_events = lambda: SimpleNamespace(damage_reports=[], effects_events=[])
  sim.debug_get_aircraft_damage_state = lambda entity_id: list(sim.aircraft.get(int(entity_id), []))
  sim.debug_get_ground_contact_state = lambda entity_id: list(sim.ground.get(int(entity_id), []))
  sim.is_unit_active = lambda entity_id: True
  return sim


class AirCombatRewardSurfaceTests(unittest.TestCase):
  def test_first_release_bonus_is_awarded_once_on_missile_count_drop(self) -> None:
    loader = _loader(
      {
        "air_combat_release_shaping_enabled": True,
        "air_combat_first_release_bonus": 300.0,
        "air_combat_repeat_release_penalty": -150.0,
        "air_combat_invalid_fire_penalty": -0.05,
      }
    )
    truth = SimpleNamespace(missiles_remaining=3, health=100.0)

    reward, terminated, truncated, status, terms, reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertEqual(reward, 300.0)
    self.assertFalse(terminated)
    self.assertFalse(truncated)
    self.assertIsNone(reason)
    self.assertEqual(status, [0.0, 0.0, 0.0, 0.0])
    self.assertEqual(terms["air_combat_first_release_bonus"], 300.0)
    self.assertEqual(loader._air_combat_reward_prev_missiles, 3)
    self.assertEqual(loader._air_combat_reward_release_count, 1)

  def test_invalid_fire_penalty_uses_effective_hybrid_pulse_without_release(self) -> None:
    loader = _loader(
      {
        "air_combat_release_shaping_enabled": True,
        "air_combat_first_release_bonus": 300.0,
        "air_combat_invalid_fire_penalty": -0.05,
      }
    )
    loader._last_effective_action[9] = 1.0
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, -0.05, places=6)
    self.assertAlmostEqual(terms["air_combat_invalid_fire_penalty"], -0.05, places=6)
    self.assertEqual(loader._air_combat_reward_prev_missiles, 4)
    self.assertEqual(loader._air_combat_reward_release_count, 0)

  def test_c2_roe_hold_fire_bonus_is_additive_when_no_fire_attempt_occurs(self) -> None:
    loader = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_hold_fire_bonus": 0.25,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 1,
        "engage_order_state": 3,
        "shot_policy_state": 0,
        "shot_budget_remaining": 0,
        "pending_assessment": False,
        "authorization_to_fire": False,
      }
    )
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, 0.25, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_hold_fire_bonus"], 0.25, places=6)
    self.assertNotIn("air_combat_invalid_fire_penalty", terms)

  def test_c2_roe_hold_fire_violation_penalizes_fire_attempt_without_release(self) -> None:
    loader = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_hold_fire_violation_penalty": -2.5,
        "air_combat_roe_authorized_fire_attempt_bonus": 1.0,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 1,
        "engage_order_state": 3,
        "shot_policy_state": 0,
        "shot_budget_remaining": 0,
        "pending_assessment": False,
        "authorization_to_fire": False,
      }
    )
    loader._last_effective_action[9] = 1.0
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, -2.5, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_hold_fire_violation_penalty"], -2.5, places=6)
    self.assertNotIn("air_combat_roe_authorized_fire_attempt_bonus", terms)

  def test_c2_roe_event_action_config_can_disable_legality_penalty_terms(self) -> None:
    loader = _loader(
      {
        "air_combat_release_shaping_enabled": True,
        "air_combat_invalid_fire_penalty": 0.0,
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_hold_fire_bonus": 0.0,
        "air_combat_roe_hold_fire_violation_penalty": 0.0,
        "air_combat_roe_unauthorized_fire_penalty": 0.0,
        "air_combat_roe_pending_assessment_penalty": 0.0,
        "air_combat_roe_premature_second_shot_penalty": 0.0,
        "air_combat_roe_shot_budget_violation_penalty": 0.0,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 1,
        "engage_order_state": 3,
        "shot_policy_state": 0,
        "shot_budget_remaining": 0,
        "pending_assessment": False,
        "authorization_to_fire": False,
      }
    )
    loader._last_effective_action[9] = 1.0
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, 0.0, places=6)
    for legality_key in (
      "air_combat_invalid_fire_penalty",
      "air_combat_roe_hold_fire_bonus",
      "air_combat_roe_hold_fire_violation_penalty",
      "air_combat_roe_unauthorized_fire_penalty",
      "air_combat_roe_pending_assessment_penalty",
      "air_combat_roe_premature_second_shot_penalty",
      "air_combat_roe_shot_budget_violation_penalty",
    ):
      self.assertNotIn(legality_key, terms)

  def test_c2_roe_authorized_weapon_chain_shaping_rewards_pre_release_actions(self) -> None:
    loader = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_authorized_radar_active_bonus": 0.1,
        "air_combat_roe_authorized_tms_up_bonus": 0.2,
        "air_combat_roe_authorized_master_arm_bonus": 0.3,
        "air_combat_roe_authorized_weapon_selected_bonus": 0.4,
        "air_combat_roe_authorized_fire_attempt_bonus": 1.0,
        "air_combat_roe_authorized_fire_no_release_penalty": -0.25,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 2,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 1,
        "pending_assessment": False,
        "authorization_to_fire": True,
      }
    )
    loader._last_effective_action[6] = 1.0
    loader._last_effective_action[7] = 1.0
    loader._last_effective_action[8] = 1.0
    loader._last_effective_action[9] = 1.0
    loader._last_effective_action[11] = 1.0
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, 1.75, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_authorized_radar_active_bonus"], 0.1, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_authorized_tms_up_bonus"], 0.2, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_authorized_master_arm_bonus"], 0.3, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_authorized_weapon_selected_bonus"], 0.4, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_authorized_fire_attempt_bonus"], 1.0, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_authorized_fire_no_release_penalty"], -0.25, places=6)

  def test_c2_roe_authorized_fire_opportunity_penalty_only_applies_before_release(self) -> None:
    loader = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_authorized_fire_opportunity_penalty": -0.5,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 2,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 1,
        "pending_assessment": False,
        "authorization_to_fire": True,
      }
    )
    loader._last_effective_action[9] = 0.0
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, -0.5, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_authorized_fire_opportunity_penalty"], -0.5, places=6)

    loader_pending = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_authorized_fire_opportunity_penalty": -0.5,
      }
    )
    loader_pending.mission_cmd.update(
      {
        "wcs_state": 2,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 0,
        "pending_assessment": True,
        "authorization_to_fire": True,
      }
    )
    loader_pending._last_effective_action[9] = 0.0

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader_pending,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, 0.0, places=6)
    self.assertNotIn("air_combat_roe_authorized_fire_opportunity_penalty", terms)

  def test_c2_roe_authorized_weapon_chain_bonus_is_awarded_once_per_episode(self) -> None:
    loader = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_authorized_radar_active_bonus": 0.1,
        "air_combat_roe_authorized_master_arm_bonus": 0.3,
        "air_combat_roe_authorized_weapon_selected_bonus": 0.4,
        "air_combat_roe_authorized_fire_attempt_bonus": 1.0,
        "air_combat_roe_authorized_fire_no_release_penalty": -0.25,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 2,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 1,
        "pending_assessment": False,
        "authorization_to_fire": True,
      }
    )
    loader._last_effective_action[6] = 1.0
    loader._last_effective_action[8] = 1.0
    loader._last_effective_action[9] = 1.0
    loader._last_effective_action[11] = 1.0
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    first_reward, *_first_rest = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )
    second_reward, _terminated, _truncated, _status, second_terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(first_reward, 1.55, places=6)
    self.assertAlmostEqual(second_reward, -0.25, places=6)
    self.assertNotIn("air_combat_roe_authorized_radar_active_bonus", second_terms)
    self.assertNotIn("air_combat_roe_authorized_master_arm_bonus", second_terms)
    self.assertNotIn("air_combat_roe_authorized_weapon_selected_bonus", second_terms)
    self.assertNotIn("air_combat_roe_authorized_fire_attempt_bonus", second_terms)
    self.assertAlmostEqual(second_terms["air_combat_roe_authorized_fire_no_release_penalty"], -0.25, places=6)

  def test_c2_roe_authorized_weapon_chain_shaping_stops_after_single_shot_budget(self) -> None:
    loader = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_authorized_fire_attempt_bonus": 1.0,
        "air_combat_roe_authorized_fire_no_release_penalty": -0.25,
        "air_combat_roe_premature_second_shot_penalty": -3.0,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 2,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 1,
        "pending_assessment": False,
        "authorization_to_fire": True,
      }
    )
    loader._air_combat_reward_release_count = 1
    loader._last_effective_action[9] = 1.0
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, -3.0, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_premature_second_shot_penalty"], -3.0, places=6)
    self.assertNotIn("air_combat_roe_authorized_fire_attempt_bonus", terms)
    self.assertNotIn("air_combat_roe_authorized_fire_no_release_penalty", terms)

  def test_c2_roe_authorized_salvo_release_gets_valid_and_salvo_terms(self) -> None:
    loader = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_valid_authorized_release_bonus": 1.0,
        "air_combat_roe_authorized_first_release_bonus": 2.0,
        "air_combat_roe_authorized_salvo_bonus": 3.0,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 2,
        "engage_order_state": 2,
        "shot_policy_state": 2,
        "shot_budget_remaining": 2,
        "pending_assessment": False,
        "authorization_to_fire": True,
      }
    )
    loader._last_effective_action[9] = 1.0
    truth = SimpleNamespace(missiles_remaining=3, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, 6.0, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_valid_authorized_release_bonus"], 1.0, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_authorized_first_release_bonus"], 2.0, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_authorized_salvo_bonus"], 3.0, places=6)
    self.assertEqual(loader._air_combat_reward_release_count, 1)

  def test_c2_roe_shot_budget_violation_blocks_authorized_release_bonus(self) -> None:
    loader = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_valid_authorized_release_bonus": 1.0,
        "air_combat_roe_shot_budget_violation_penalty": -4.0,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 2,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 0,
        "pending_assessment": False,
        "authorization_to_fire": True,
      }
    )
    loader._last_effective_action[9] = 1.0
    truth = SimpleNamespace(missiles_remaining=3, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, -4.0, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_shot_budget_violation_penalty"], -4.0, places=6)
    self.assertNotIn("air_combat_roe_valid_authorized_release_bonus", terms)

  def test_c2_roe_pending_assessment_violation_is_separate_from_unauthorized_fire(self) -> None:
    loader = _loader(
      {
        "air_combat_c2_roe_release_discipline_enabled": True,
        "air_combat_roe_pending_assessment_penalty": -3.0,
        "air_combat_roe_unauthorized_fire_penalty": -5.0,
      }
    )
    loader.mission_cmd.update(
      {
        "wcs_state": 2,
        "engage_order_state": 2,
        "shot_policy_state": 1,
        "shot_budget_remaining": 1,
        "pending_assessment": True,
        "authorization_to_fire": True,
      }
    )
    loader._air_combat_reward_release_count = 1
    loader._last_effective_action[9] = 1.0
    truth = SimpleNamespace(missiles_remaining=3, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      _sim(),
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, -3.0, places=6)
    self.assertAlmostEqual(terms["air_combat_roe_pending_assessment_penalty"], -3.0, places=6)
    self.assertNotIn("air_combat_roe_unauthorized_fire_penalty", terms)

  def test_damage_shaping_transitional_damage_report_fallback_is_consumed_once(self) -> None:
    loader = _loader({"air_combat_damage_shaping_enabled": True})
    sim = _event_sim(damage_reports=[_damage_report()])
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, 632.0, places=6)
    self.assertAlmostEqual(terms["air_combat_target_system_damage_progress"], 5.0, places=6)
    self.assertAlmostEqual(terms["air_combat_target_mission_capability_progress"], 0.4, places=6)
    self.assertAlmostEqual(terms["air_combat_target_mobility_capability_progress"], 0.6, places=6)
    self.assertAlmostEqual(terms["air_combat_target_survivability_capability_progress"], 1.0, places=6)
    self.assertAlmostEqual(terms["air_combat_target_mission_kill_progress"], 125.0, places=6)
    self.assertAlmostEqual(terms["air_combat_target_survivability_kill_progress"], 250.0, places=6)
    self.assertAlmostEqual(terms["air_combat_target_lost_progress"], 250.0, places=6)

    second_reward, _terminated2, _truncated2, _status2, second_terms, _reason2 = (
      apply_air_combat_reward_surface(
        loader,
        sim,
        truth,
        reward=0.0,
        terminated=False,
        truncated=False,
        status=[0.0, 0.0, 0.0, 0.0],
        reward_breakdown={},
      )
    )

    self.assertAlmostEqual(second_reward, 0.0, places=6)
    self.assertNotIn("air_combat_target_system_damage_progress", second_terms)

  def test_damage_shaping_prefers_standard_events_without_damage_report_delta(self) -> None:
    rewards = {"air_combat_damage_shaping_enabled": True}
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)
    fallback_loader = _loader(rewards)
    standard_loader = _loader(rewards)
    fallback_sim = _event_sim(damage_reports=[_damage_report()])
    standard_sim = _event_sim(
      platform_consequence_events=[_platform_consequence_event()],
      lifecycle_transition_events=[_lifecycle_transition_event()],
    )

    fallback_reward, *_fallback_rest, fallback_terms, _fallback_reason = (
      apply_air_combat_reward_surface(
        fallback_loader,
        fallback_sim,
        truth,
        reward=0.0,
        terminated=False,
        truncated=False,
        status=[0.0, 0.0, 0.0, 0.0],
        reward_breakdown={},
      )
    )
    standard_reward, *_standard_rest, standard_terms, _standard_reason = (
      apply_air_combat_reward_surface(
        standard_loader,
        standard_sim,
        truth,
        reward=0.0,
        terminated=False,
        truncated=False,
        status=[0.0, 0.0, 0.0, 0.0],
        reward_breakdown={},
      )
    )

    self.assertAlmostEqual(standard_reward, fallback_reward, places=6)
    self.assertEqual(set(standard_terms), set(fallback_terms))
    for key, value in fallback_terms.items():
      self.assertAlmostEqual(standard_terms[key], value, places=6)

  def test_diagnostics_only_platform_consequence_event_does_not_shape_reward(self) -> None:
    loader = _loader({"air_combat_damage_shaping_enabled": True})
    sim = _event_sim(
      platform_consequence_events=[
        _platform_consequence_event(consumer_visibility="diagnostics_only")
      ]
    )
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, 0.0, places=6)
    self.assertNotIn("air_combat_target_system_damage_progress", terms)
    self.assertNotIn("air_combat_target_mission_kill_progress", terms)

  def test_standard_lifecycle_terminal_state_does_not_need_damage_report(self) -> None:
    loader = _loader({"air_combat_damage_terminal_enabled": True})
    sim = _event_sim(lifecycle_transition_events=[_lifecycle_transition_event()])

    state = combat_entity_terminal_state(loader, sim, 2)

    self.assertTrue(state["neutralized"])
    self.assertFalse(state["actionable"])
    self.assertEqual(state["reason"], "lost")
    self.assertEqual(state["loss_state"], "lost")
    self.assertEqual(state["lifecycle_event_id"], 8)
    self.assertEqual(state["damage_report_id"], 0)

  def test_standard_lifecycle_ground_terminal_requires_crashed_wreck_lifecycle(self) -> None:
    loader = _loader({"air_combat_damage_terminal_enabled": True})
    safe_sim = _event_sim(
      lifecycle_transition_events=[
        _lifecycle_transition_event(
          lifecycle_to="ground_contact",
          ground_lifecycle="1",
          terminal=True,
        )
      ]
    )
    crash_sim = _event_sim(
      lifecycle_transition_events=[
        _lifecycle_transition_event(
          lifecycle_to="ground_crashed_wreck",
          ground_lifecycle="2",
          terminal=True,
        )
      ]
    )

    safe_state = combat_entity_terminal_state(loader, safe_sim, 2)
    crash_state = combat_entity_terminal_state(loader, crash_sim, 2)

    self.assertFalse(safe_state["neutralized"])
    self.assertTrue(safe_state["actionable"])
    self.assertEqual(safe_state["reason"], "")
    self.assertTrue(crash_state["neutralized"])
    self.assertFalse(crash_state["actionable"])
    self.assertEqual(crash_state["reason"], "ground_crashed_wreck")
    self.assertEqual(crash_state["ground_lifecycle"], 2)

  def test_damage_consequence_shaping_rewards_target_deltas_once(self) -> None:
    loader = _loader(
      {
        "air_combat_damage_shaping_enabled": False,
        "air_combat_target_damage_consequence_fire_severity_scale": 10.0,
        "air_combat_target_damage_consequence_fuel_leak_severity_scale": 20.0,
        "air_combat_target_damage_consequence_propulsion_integrity_scale": 30.0,
      }
    )
    sim = _consequence_sim(aircraft={2: _aircraft_damage_state()})
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    reward, *_rest = apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )
    self.assertAlmostEqual(reward, 0.0, places=6)

    sim.aircraft[2] = _aircraft_damage_state(
      propulsion_integrity=0.7,
      fuel_leak_severity=0.25,
      fire_severity=0.2,
    )
    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, 16.0, places=6)
    self.assertAlmostEqual(
      terms["air_combat_target_damage_consequence_propulsion_integrity_progress"],
      9.0,
      places=6,
    )
    self.assertAlmostEqual(
      terms["air_combat_target_damage_consequence_fuel_leak_severity_progress"],
      5.0,
      places=6,
    )
    self.assertAlmostEqual(
      terms["air_combat_target_damage_consequence_fire_severity_progress"],
      2.0,
      places=6,
    )

    reward2, _terminated2, _truncated2, _status2, terms2, _reason2 = apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )
    self.assertAlmostEqual(reward2, 0.0, places=6)
    self.assertNotIn("air_combat_target_damage_consequence_propulsion_integrity_progress", terms2)

  def test_damage_consequence_shaping_penalizes_self_damage_transitions(self) -> None:
    loader = _loader(
      {
        "air_combat_damage_shaping_enabled": False,
        "air_combat_damage_consequence_shaping_enabled": True,
        "air_combat_self_damage_consequence_flight_control_integrity_scale": 8.0,
        "air_combat_self_damage_consequence_flight_control_kill_scale": 100.0,
      }
    )
    sim = _consequence_sim(aircraft={1: _aircraft_damage_state()})
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    sim.aircraft[1] = _aircraft_damage_state(
      flight_control_integrity=0.5,
      flight_control_kill=1.0,
    )
    reward, _terminated, _truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    self.assertAlmostEqual(reward, -104.0, places=6)
    self.assertAlmostEqual(
      terms["air_combat_self_damage_consequence_flight_control_integrity_penalty"],
      -4.0,
      places=6,
    )
    self.assertAlmostEqual(
      terms["air_combat_self_damage_consequence_flight_control_kill_penalty"],
      -100.0,
      places=6,
    )

  def test_damage_consequence_ground_rewards_crash_not_safe_contact(self) -> None:
    loader = _loader(
      {
        "air_combat_damage_shaping_enabled": False,
        "air_combat_damage_consequence_shaping_enabled": True,
        "air_combat_target_damage_consequence_ground_crashed_wreck_scale": 200.0,
        "air_combat_target_damage_consequence_ground_gear_collapse_scale": 75.0,
        "air_combat_target_damage_consequence_ground_impact_scale": 50.0,
      }
    )
    sim = _consequence_sim(ground={2: _ground_contact_state()})
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    sim.ground[2] = _ground_contact_state(on_ground=1.0, lifecycle=1.0, impact_severity=0.4)
    safe_reward, _terminated, _truncated, _status, safe_terms, _reason = apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )
    self.assertAlmostEqual(safe_reward, 0.0, places=6)
    self.assertNotIn("air_combat_target_damage_consequence_ground_crashed_wreck_progress", safe_terms)
    self.assertNotIn("air_combat_target_damage_consequence_ground_impact_progress", safe_terms)

    sim.ground[2] = _ground_contact_state(
      on_ground=1.0,
      lifecycle=2.0,
      impact_severity=1.4,
      gear_collapsed=1.0,
    )
    crash_reward, _terminated2, _truncated2, _status2, crash_terms, _reason2 = (
      apply_air_combat_reward_surface(
        loader,
        sim,
        truth,
        reward=0.0,
        terminated=False,
        truncated=False,
        status=[0.0, 0.0, 0.0, 0.0],
        reward_breakdown={},
      )
    )

    self.assertAlmostEqual(crash_reward, 295.0, places=6)
    self.assertAlmostEqual(
      crash_terms["air_combat_target_damage_consequence_ground_crashed_wreck_progress"],
      200.0,
      places=6,
    )
    self.assertAlmostEqual(
      crash_terms["air_combat_target_damage_consequence_ground_gear_collapse_progress"],
      75.0,
      places=6,
    )
    self.assertAlmostEqual(
      crash_terms["air_combat_target_damage_consequence_ground_impact_progress"],
      20.0,
      places=6,
    )

  def test_combat_terminal_state_treats_crashed_ground_contact_as_neutralized(self) -> None:
    loader = _loader({"air_combat_damage_terminal_enabled": True})
    sim = _consequence_sim(
      ground={
        2: _ground_contact_state(
          on_ground=1.0,
          lifecycle=2.0,
          impact_h_speed=56.0,
          impact_sink_rate=4.0,
          impact_severity=1.4,
        )
      }
    )

    state = combat_entity_terminal_state(loader, sim, 2)

    self.assertTrue(state["neutralized"])
    self.assertFalse(state["actionable"])
    self.assertEqual(state["reason"], "ground_crashed_wreck")
    self.assertEqual(state["loss_state"], "ground_crashed_wreck")
    self.assertEqual(state["ground_lifecycle"], 2)
    self.assertAlmostEqual(state["ground_impact_severity"], 1.4, places=6)

  def test_combat_terminal_state_keeps_safe_ground_contact_actionable(self) -> None:
    loader = _loader({"air_combat_damage_terminal_enabled": True})
    sim = _consequence_sim(
      ground={
        2: _ground_contact_state(
          on_ground=1.0,
          lifecycle=1.0,
          impact_h_speed=7.0,
          impact_sink_rate=0.5,
          impact_severity=0.2,
        )
      }
    )

    state = combat_entity_terminal_state(loader, sim, 2)

    self.assertFalse(state["neutralized"])
    self.assertTrue(state["actionable"])
    self.assertEqual(state["reason"], "")

  def test_damage_consequence_ground_transition_is_kept_on_terminal_step(self) -> None:
    loader = _loader(
      {
        "air_combat_damage_shaping_enabled": False,
        "air_combat_damage_consequence_shaping_enabled": True,
        "air_combat_target_damage_consequence_ground_crashed_wreck_scale": 200.0,
        "air_combat_target_damage_consequence_ground_impact_scale": 0.0,
      }
    )
    sim = _consequence_sim(ground={2: _ground_contact_state()})
    truth = SimpleNamespace(missiles_remaining=4, health=100.0)

    apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=0.0,
      terminated=False,
      truncated=False,
      status=[0.0, 0.0, 0.0, 0.0],
      reward_breakdown={},
    )

    sim.ground[2] = _ground_contact_state(on_ground=1.0, lifecycle=2.0, impact_severity=1.2)
    reward, terminated, truncated, _status, terms, _reason = apply_air_combat_reward_surface(
      loader,
      sim,
      truth,
      reward=1500.0,
      terminated=True,
      truncated=False,
      status=[0.0, 0.0, 0.0, 1.0],
      reward_breakdown={"combat_win_bonus": 1500.0},
    )

    self.assertTrue(terminated)
    self.assertFalse(truncated)
    self.assertAlmostEqual(reward, 1700.0, places=6)
    self.assertAlmostEqual(
      terms["air_combat_target_damage_consequence_ground_crashed_wreck_progress"],
      200.0,
      places=6,
    )


if __name__ == "__main__":
  unittest.main()
