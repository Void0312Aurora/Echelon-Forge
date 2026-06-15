from __future__ import annotations

import math
import os
import tempfile
import unittest
from argparse import Namespace
from types import SimpleNamespace

import numpy as np
import torch as th

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from tools.diagnostics import air_combat_weapon_employment_process_probe as probe # noqa: E402


class _DummyHybridDistribution:
  def __init__(self) -> None:
    self.binary_logits = th.tensor([[3.0, -1.0, 2.0, -0.5, -6.0]], dtype=th.float32)
    self.fire_event_mask = th.tensor([[1, 1]], dtype=th.bool)
    self.categorical_logits = [
      (11, th.tensor([[-1.0, 2.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0]], dtype=th.float32))
    ]

  def _fire_event_logits(self):
    return th.tensor([[1.0, 3.0]], dtype=th.float32)


def _entity(entity_id: int) -> SimpleNamespace:
  return SimpleNamespace(entity_id=int(entity_id), world_index=0)


def _header(
  *,
  chain_id: int,
  event_id: int,
  parent_event_id: int,
  stage: str,
  status: str,
  reason: str,
  munition_id: int = 501,
  target_id: int = 200,
) -> SimpleNamespace:
  return SimpleNamespace(
    schema_version=1,
    chain_id=int(chain_id),
    event_id=int(event_id),
    parent_event_id=int(parent_event_id),
    stage=str(stage),
    status=str(status),
    reason=str(reason),
    source_time_s=4.25,
    source_frame=0,
    munition=_entity(munition_id),
    shooter=_entity(100),
    target=_entity(target_id),
    producer_node_id="test",
    fidelity_mode="runtime",
    evidence_level="observed_runtime",
    confidence=1.0,
  )


def _standard_nearest_event(reason: str = "fuze_no_detonation") -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=102,
      parent_event_id=301,
      stage="nearest_approach",
      status="observed",
      reason=reason,
    ),
    nearest_approach_time_s=4.25,
    miss_distance_m=12.5,
    local_forward_m=1.0,
    local_right_m=2.0,
    local_up_m=2.0,
    closure_mps=725.0,
    aspect_bucket="beam",
  )


def _standard_fuze_event(
  *,
  reason: str = "fuze_no_detonation",
  armed: bool = True,
  triggered: bool = False,
) -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=103,
      parent_event_id=102,
      stage="fuze",
      status="evaluated",
      reason=reason,
    ),
    fuze_type="radar_proximity",
    armed=armed,
    triggered=triggered,
    failure_reason="" if triggered else reason,
    delay_s=0.0,
    reliability=0.0 if not triggered else 0.98,
    sample=0.42,
    trigger_radius_m=35.0,
    contact_surface_distance_m=0.0,
    contact_penetration_depth_m=0.0,
    contact_surface_tolerance_m=0.0,
    contact_inside_hitbox=False,
    direct_hitbox_intersection=False,
  )


def _standard_warhead_event() -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=104,
      parent_event_id=101,
      stage="warhead_mechanism",
      status="applied",
      reason="generic_research_warhead_profile",
      target_id=200,
    ),
    mechanism_family="blast_fragmentation",
    warhead_mass_kg=12.0,
    lethal_radius_m=35.0,
    fragment_energy_j=540.0,
    fragment_density_per_m2=17.0,
    blast_overpressure_kpa=18.0,
    blast_impulse_kpa_ms=41.0,
    blast_scaled_distance_m_kg13=2.5,
    rod_cut_margin=0.0,
    penetration_margin=0.35,
    surface_incidence_cos=0.8,
  )


def _standard_spatial_event() -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=105,
      parent_event_id=101,
      stage="spatial_coverage",
      status="projected",
      reason="generic_research_spatial_projection",
      target_id=200,
    ),
    projected_hitbox_count=4,
    sample_count=360,
    hit_estimate=1.8,
    hit_fraction=0.005,
    energy_scale=0.74,
    pattern_scale=1.1,
  )


def _standard_component_load_event() -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=106,
      parent_event_id=101,
      stage="component_load",
      status="projected",
      reason="generic_research_component_load_projection",
      target_id=200,
    ),
    component_name="right_aileron_actuator",
    component_system="flight_control",
    direct_hit=True,
    distance_m=0.7,
    effect_scale=0.83,
    fragment_energy_j=420.0,
    fragment_density_per_m2=13.0,
    blast_overpressure_kpa=14.0,
    blast_impulse_kpa_ms=32.0,
    blast_scaled_distance_m_kg13=2.7,
    rod_cut_margin=0.0,
    penetration_margin=0.25,
    surface_incidence_cos=0.9,
    load_source="direct_component_hit",
  )


def _standard_component_damage_event() -> SimpleNamespace:
  return SimpleNamespace(
    header=_header(
      chain_id=301,
      event_id=107,
      parent_event_id=106,
      stage="component_damage",
      status="sampled",
      reason="generic_research_component_damage_candidate",
      target_id=200,
    ),
    component_name="right_aileron_actuator",
    component_system="flight_control",
    component_redundancy_group_id="flight_control:right_aileron",
    integrity_before=1.0,
    integrity_after=0.68,
    failure_mode="cut",
    failure_severity=0.74,
    failure_probability=0.82,
    failure_sample=0.21,
  )


def _effect_component_damage_row(*, sample: float = 0.21) -> SimpleNamespace:
  return SimpleNamespace(
    component_name="right_aileron_actuator",
    component_system="flight_control",
    direct_hit=True,
    effect_scale=0.83,
    mechanism_fragment_energy_j=420.0,
    mechanism_fragment_areal_density_per_m2=13.0,
    mechanism_blast_overpressure_kpa=14.0,
    mechanism_blast_impulse_kpa_ms=32.0,
    mechanism_blast_scaled_distance_m_kg13=2.7,
    mechanism_rod_cut_margin=0.0,
    mechanism_penetration_margin=0.25,
    mechanism_surface_incidence_cos=0.9,
    component_integrity_before=1.0,
    component_integrity_after=0.68,
    component_failure_primary_mode="cut",
    component_failure_primary_mode_severity=0.74,
    component_failure_probability=0.82,
    component_failure_sample=sample,
  )


def _dummy_lethality_events() -> SimpleNamespace:
  effect = SimpleNamespace(
    event_id=101,
    munition=_entity(501),
    target=_entity(200),
    miss_distance_m=12.5,
    nearest_approach_time_s=4.25,
    detonation_local_forward_m=1.0,
    detonation_local_right_m=2.0,
    detonation_local_up_m=2.0,
    fuze_type="proximity",
    direct_hitbox_intersection=True,
    effect_family="blast_fragmentation",
    warhead_mass_kg=12.0,
    warhead_lethal_radius_m=35.0,
    mechanism_fragment_energy_j=540.0,
    mechanism_fragment_areal_density_per_m2=17.0,
    mechanism_blast_overpressure_kpa=18.0,
    mechanism_blast_impulse_kpa_ms=41.0,
    mechanism_blast_scaled_distance_m_kg13=2.5,
    mechanism_rod_cut_margin=0.0,
    mechanism_penetration_margin=0.35,
    mechanism_surface_incidence_cos=0.8,
    projected_hitbox_count=3,
    warhead_spatial_sample_count=240,
    warhead_spatial_hit_estimate=1.2,
    warhead_spatial_hit_fraction=0.005,
    warhead_spatial_energy_scale=0.7,
    warhead_spatial_pattern_scale=1.0,
    component_hit_count=2,
    component_mechanism_load_rows=[_effect_component_damage_row()],
    fuze_profile_synthetic=True,
    warhead_profile_synthetic=True,
    damage_scalar_synthetic=True,
    vulnerability_calibrated_evidence=False,
  )
  report = SimpleNamespace(
    report_id=201,
    target=_entity(200),
    source_event_id=101,
    system_health_delta=-0.35,
    mission_kill=True,
    mobility_kill=False,
    sensor_kill=True,
    destroyed=True,
    loss_state_to="lost",
  )
  trace = SimpleNamespace(
    chain_id=301,
    launch_event_id=301,
    effects_event_id=101,
    damage_report_id=201,
    munition=_entity(501),
  )
  return SimpleNamespace(
    effects_events=[effect],
    damage_reports=[report],
    diagnostics_traces=[trace],
    nearest_approach_events=[],
    fuze_evaluation_events=[],
    warhead_mechanism_events=[],
    spatial_coverage_events=[],
    component_load_events=[],
    component_damage_events=[],
  )


class DiagnosticsProcessProbeSnapshotTests(unittest.TestCase):
  def test_run_probe_payload_and_chain_csv_include_lethality_chain_rows(self) -> None:
    class DummyInstrumentState:
      ias = 180.0
      alt_baro = 1200.0
      alt_radar = 900.0
      pitch = 2.0
      roll = 0.5
      aoa = 1.0

    class DummyUnit:
      def __init__(self, unit_id: int) -> None:
        self.id = unit_id

    class DummySim:
      def __init__(self) -> None:
        self.time = 0.0
        self.events = SimpleNamespace(effects_events=[], damage_reports=[], diagnostics_traces=[])

      def get_agent_observation(self, _agent_id: int):
        return SimpleNamespace(
          contacts=[],
          missiles_remaining=2,
          sim_time=self.time,
          health=100.0,
          can_fire=False,
        )

      def get_instrument_state(self, _agent_id: int):
        return DummyInstrumentState()

      def get_all_units(self):
        return [DummyUnit(100), DummyUnit(200)]

      def is_unit_active(self, _unit_id: int) -> bool:
        return True

      def get_unit_health(self, _unit_id: int):
        return [75.0]

      def get_unit_position(self, unit_id: int):
        return (0.0, 0.0, 0.0) if unit_id == 100 else (3000.0, 4000.0, 0.0)

      def get_time_step(self) -> float:
        return 0.1

      def export_recent_engagement_events(self):
        return self.events

    class DummyEnv:
      def __init__(self) -> None:
        self.sim = DummySim()
        self.agent_id = 100
        self.loader = SimpleNamespace(primary_target_id=200, mission_cmd={})
        self.action_mode = "air_combat_hybrid_v1"
        self.unwrapped = self

      def reset(self, seed: int | None = None):
        self.sim.time = 0.0
        self.sim.events = SimpleNamespace(effects_events=[], damage_reports=[], diagnostics_traces=[])
        return {}, {}

      def step(self, _action):
        self.sim.time = 0.1
        self.sim.events = _dummy_lethality_events()
        return {}, 0.0, True, False, {"termination_reason": "combat_timeout", "reward_terms": {}}

      def close(self) -> None:
        pass

    old_build_env = probe._build_env
    try:
      probe._build_env = lambda *_args, **_kwargs: DummyEnv()
      with tempfile.TemporaryDirectory() as tmpdir:
        chain_csv_out = os.path.join(tmpdir, "chain.csv")
        payload = probe.run_probe(
          Namespace(
            scenario="dummy.json",
            train_config="",
            mode="hold_fire",
            fire_range_m=12000.0,
            fire_delay_steps=0,
            legal_fire_range_m=0.0,
            model="",
            algo="auto",
            device="auto",
            episodes=1,
            seed=17,
            max_steps=1,
            stochastic=False,
            csv_out="",
            chain_csv_out=chain_csv_out,
            json_out="",
            plot_out="",
          )
        )

        self.assertIn("lethality_chain_rows", payload)
        self.assertEqual(len(payload["lethality_chain_rows"]), len(probe.LETHALITY_CHAIN_STAGES))
        self.assertEqual(
          payload["episode_summaries"][0]["lethality_chain_row_count"],
          len(probe.LETHALITY_CHAIN_STAGES),
        )
        self.assertEqual(payload["episode_summaries"][0]["lethality_chain_chain_count"], 1)
        self.assertTrue(os.path.exists(chain_csv_out))
        with open(chain_csv_out, "r", encoding="utf-8") as f:
          header = f.readline().strip().split(",")
        self.assertIn("chain_id", header)
        self.assertIn("stage", header)
        self.assertNotIn("last_effect_miss_distance_m", header)
        self.assertNotIn("last_damage_report_id", header)
    finally:
      probe._build_env = old_build_env

  def test_snapshot_row_aggregates_damage_consequence_reward_terms(self) -> None:
    class DummyTrack:
      id = 200
      range = 5000.0
      closing_speed = 250.0
      time_since_update = 0.2

    class DummyTruth:
      contacts = [DummyTrack()]
      missiles_remaining = 2
      sim_time = 4.0
      health = 100.0
      can_fire = False

    class DummyInstrumentState:
      ias = 180.0
      alt_baro = 1200.0
      alt_radar = 900.0
      pitch = 2.0
      roll = 0.5
      aoa = 1.0

    class DummyUnit:
      def __init__(self, unit_id: int) -> None:
        self.id = unit_id

    class DummyEngagementEvents:
      effects_events = []
      damage_reports = []

    class DummySim:
      def get_agent_observation(self, _agent_id: int):
        return DummyTruth()

      def get_instrument_state(self, _agent_id: int):
        return DummyInstrumentState()

      def get_all_units(self):
        return [DummyUnit(100), DummyUnit(200)]

      def is_unit_active(self, _unit_id: int) -> bool:
        return True

      def get_unit_health(self, _unit_id: int):
        return [75.0]

      def get_unit_position(self, unit_id: int):
        return (0.0, 0.0, 0.0) if unit_id == 100 else (3000.0, 4000.0, 0.0)

      def get_time_step(self) -> float:
        return 0.1

      def export_recent_engagement_events(self):
        return DummyEngagementEvents()

    class DummyLoader:
      primary_target_id = 200
      mission_cmd = {}

    class DummyEnv:
      sim = DummySim()
      agent_id = 100
      loader = DummyLoader()
      action_mode = "air_combat_hybrid_v1"

    row = probe._snapshot_row(
      episode=0,
      step=4,
      env=DummyEnv(),
      action=None,
      reward=0.0,
      terminated=False,
      truncated=False,
      info={
        "reward_terms": {
          "air_combat_target_damage_consequence_propulsion_integrity_progress": 0.25,
          "air_combat_target_damage_consequence_fire_severity_progress": "0.5",
          "air_combat_self_damage_consequence_flight_control_integrity_penalty": -0.125,
          "air_combat_self_damage_consequence_nonfinite_penalty": math.nan,
          "air_combat_damage_consequence_unscoped": 99.0,
        }
      },
      initial_units={100, 200},
      prev_missiles=2,
    )

    self.assertAlmostEqual(row["target_damage_consequence_reward_total"], 0.75, places=6)
    self.assertAlmostEqual(row["self_damage_consequence_reward_total"], -0.125, places=6)
    self.assertAlmostEqual(row["damage_consequence_reward_total"], 0.625, places=6)

  def test_episode_summary_reports_damage_consequence_reward_totals(self) -> None:
    def row(step: int, *, target_reward: float = 0.0, self_reward: float = 0.0) -> dict:
      total = target_reward + self_reward
      return {
        "episode": 0,
        "step": step,
        "reward": total,
        "terminated": int(step == 3),
        "truncated": 0,
        "termination_reason": "combat_timeout" if step == 3 else "",
        "target_range_geom_m": 12000.0 - step,
        "target_health": 100.0,
        "target_active": 1,
        "missiles_remaining": 4,
        "missile_release": 0,
        "damage_consequence_reward_total": total,
        "target_damage_consequence_reward_total": target_reward,
        "self_damage_consequence_reward_total": self_reward,
      }

    summary = probe._summarize_episode(
      [
        row(0, target_reward=100.0),
        row(1, self_reward=-0.2),
        row(2, target_reward=0.5),
        row(3, target_reward=0.25),
      ]
    )

    self.assertAlmostEqual(summary["target_damage_consequence_reward_total"], 0.75, places=6)
    self.assertAlmostEqual(summary["self_damage_consequence_reward_total"], -0.2, places=6)
    self.assertAlmostEqual(summary["damage_consequence_reward_total"], 0.55, places=6)
    self.assertEqual(summary["first_damage_consequence_reward_step"], 1)
    self.assertEqual(summary["first_target_damage_consequence_reward_step"], 2)
    self.assertEqual(summary["first_self_damage_consequence_reward_step"], 1)

  def test_controlled_consequence_bridge_record_exposes_timing_counts_and_dcr_totals(self) -> None:
    def row(
      step: int,
      *,
      release: int = 0,
      effects: int = 0,
      damage: int = 0,
      target_reward: float = 0.0,
      self_reward: float = 0.0,
    ) -> dict:
      total = target_reward + self_reward
      return {
        "episode": 0,
        "step": step,
        "reward": total,
        "terminated": int(step == 4),
        "truncated": 0,
        "termination_reason": "combat_timeout" if step == 4 else "",
        "target_range_geom_m": 12000.0 - step,
        "target_health": 100.0,
        "target_active": 1,
        "missiles_remaining": 4 - release,
        "missile_release": release,
        "missile_release_delta": release,
        "effects_event_count": effects,
        "damage_report_count": damage,
        "damage_consequence_reward_total": total,
        "target_damage_consequence_reward_total": target_reward,
        "self_damage_consequence_reward_total": self_reward,
      }

    chain_rows = [
      {
        "episode": 0,
        "chain_id": 301,
        "event_id": idx + 1,
        "stage": stage,
        "source_event_kind": "test",
        "source_event_id": idx + 1,
      }
      for idx, stage in enumerate(probe.LETHALITY_CHAIN_STAGES)
    ]
    summary = probe._summarize_episode(
      [
        row(0),
        row(1, release=1),
        row(2, effects=1, damage=1),
        row(3, effects=1, damage=1, target_reward=0.25),
        row(4, effects=1, damage=1, target_reward=0.5, self_reward=-0.1),
      ],
      lethality_chain_rows=chain_rows,
    )

    record = probe._controlled_consequence_bridge_record(summary)

    self.assertEqual(record["first_release_step"], 1)
    self.assertEqual(record["first_effects_event_step"], 2)
    self.assertEqual(record["first_damage_report_step"], 2)
    self.assertEqual(record["first_damage_consequence_reward_step"], 3)
    self.assertAlmostEqual(record["target_damage_consequence_reward_total"], 0.75, places=6)
    self.assertAlmostEqual(record["self_damage_consequence_reward_total"], -0.1, places=6)
    self.assertAlmostEqual(record["damage_consequence_reward_total"], 0.65, places=6)
    self.assertEqual(record["effects_event_count"], 1)
    self.assertEqual(record["damage_report_count"], 1)
    self.assertEqual(record["lethality_chain_row_count"], len(probe.LETHALITY_CHAIN_STAGES))
    self.assertEqual(record["lethality_chain_chain_count"], 1)
    self.assertEqual(
      record["lethality_chain_stages_json"],
      probe._stable_json(sorted(probe.LETHALITY_CHAIN_STAGES)),
    )

  def test_diagnostic_dcr_bridge_overlays_loader_rewards_without_scenario_file_edits(self) -> None:
    loader = SimpleNamespace(
      scenario_data={"rewards": {"survival": 0.0}},
      _compiled_rewards_cfg={"survival": 0.0},
    )
    env = SimpleNamespace(unwrapped=SimpleNamespace(loader=loader))
    overrides = probe._diagnostic_dcr_bridge_overrides(
      Namespace(
        diagnostic_dcr_bridge=True,
        diagnostic_dcr_target_scale=0.5,
        diagnostic_dcr_self_scale=0.25,
        diagnostic_dcr_delta_clip=0.75,
      )
    )

    probe._apply_diagnostic_dcr_bridge(env, overrides)

    self.assertEqual(loader.scenario_data["rewards"]["survival"], 0.0)
    self.assertTrue(loader.scenario_data["rewards"]["air_combat_damage_consequence_shaping_enabled"])
    self.assertAlmostEqual(
      loader.scenario_data["rewards"]["air_combat_target_damage_consequence_scale"],
      0.5,
      places=6,
    )
    self.assertAlmostEqual(
      loader.scenario_data["rewards"]["air_combat_self_damage_consequence_scale"],
      0.25,
      places=6,
    )
    self.assertAlmostEqual(
      loader._compiled_rewards_cfg["air_combat_damage_consequence_delta_clip"],
      0.75,
      places=6,
    )

  def test_build_env_applies_multi_timescale_wrapper_from_train_config(self) -> None:
    class DummyVecEnv:
      def __init__(self, **kwargs):
        self.kwargs = kwargs

    class DummyWrapper:
      pass

    old_vec_env = probe.WorldBatchVecEnv
    old_wrapper = probe.MultiTimescaleActionWrapper
    old_get_spec = probe.get_action_wrapper_spec
    try:
      probe.WorldBatchVecEnv = DummyVecEnv
      probe.MultiTimescaleActionWrapper = DummyWrapper
      probe.get_action_wrapper_spec = lambda _cfg: (DummyWrapper, {"scripted_blend_indices": [0, 1, 2, 3]})

      env = probe._build_env(
        "scenarios/air_combat/1v1/dummy.json",
        {"env": {"action_mode": "air_combat_hybrid_v1"}},
      )

      self.assertIsInstance(env, probe._BatchSingleWorldProbeEnv)
      self.assertIsInstance(env._vec_env, DummyVecEnv)
      self.assertEqual(env._vec_env.kwargs["action_mode"], "air_combat_hybrid_v1")
      self.assertEqual(
        env._vec_env.kwargs["action_wrapper_kwargs"],
        {"scripted_blend_indices": [0, 1, 2, 3]},
      )
    finally:
      probe.WorldBatchVecEnv = old_vec_env
      probe.MultiTimescaleActionWrapper = old_wrapper
      probe.get_action_wrapper_spec = old_get_spec

  def test_hybrid_forced_fire_action_uses_hybrid_layout(self) -> None:
    action = probe._forced_fire_action(
      {},
      np.random.default_rng(7),
      1,
      action_mode="air_combat_hybrid_v1",
    )

    self.assertEqual(tuple(action.shape), (12,))
    self.assertEqual(float(action[6]), 1.0)
    self.assertEqual(float(action[7]), 1.0)
    self.assertEqual(float(action[8]), 1.0)
    self.assertEqual(float(action[9]), 1.0)
    self.assertEqual(probe._weapon_select_id(action, action_mode="air_combat_hybrid_v1"), 1)

  def test_episode_summary_reports_invalid_effective_fire_attempts(self) -> None:
    def row(step: int, *, fire: int = 0, release: int = 0) -> dict:
      return {
        "episode": 0,
        "step": step,
        "reward": 0.0,
        "terminated": int(step == 3),
        "truncated": 0,
        "termination_reason": "combat_timeout" if step == 3 else "",
        "target_range_geom_m": 12000.0 - step,
        "target_health": 100.0,
        "can_fire": 1,
        "target_contact": 1,
        "target_active": 1,
        "missiles_remaining": 2 - release,
        "missile_release": release,
        "action_radar_on": 1,
        "action_master_arm_on": 1,
        "action_fire_weapon_on": fire,
        "action_radar_active": 1.0,
        "action_master_arm": 1.0,
        "action_fire_weapon": float(fire),
        "effective_action_fire_weapon": float(fire),
        "effects_event_count": 0,
        "damage_report_count": 0,
      }

    summary = probe._summarize_episode(
      [
        row(0),
        row(1, fire=1, release=1),
        row(2, fire=0, release=0),
        row(3, fire=1, release=0),
      ]
    )

    self.assertEqual(summary["fire_attempt_count"], 2)
    self.assertEqual(summary["release_count"], 1)
    self.assertEqual(summary["invalid_fire_attempt_count"], 1)
    self.assertEqual(summary["invalid_fire_attempt_steps"], [3])
    self.assertEqual(summary["invalid_fire_attempt_rate"], 0.5)



if __name__ == "__main__":
  unittest.main()
