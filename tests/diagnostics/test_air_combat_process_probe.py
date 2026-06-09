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

from tools.diagnostics import air_combat_stage0_process_probe as probe  # noqa: E402


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
            stage="fuze_evaluation",
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
        component_mechanism_load_rows=[],
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
    )


class AirCombatProcessProbeTests(unittest.TestCase):
    def test_distribution_policy_diagnostics_extract_hybrid_binary_probabilities(self) -> None:
        diagnostics = probe._distribution_policy_diagnostics(_DummyHybridDistribution())

        self.assertAlmostEqual(diagnostics["policy_logit_tms_up"], -1.0, places=6)
        self.assertAlmostEqual(diagnostics["policy_prob_tms_up"], 0.2689414, places=6)
        self.assertAlmostEqual(diagnostics["policy_logit_fire_weapon"], -0.5, places=6)
        self.assertAlmostEqual(diagnostics["policy_prob_fire_weapon"], 0.3775407, places=6)
        self.assertAlmostEqual(diagnostics["policy_event_prob_fire_once"], 0.8807970, places=6)
        self.assertEqual(int(diagnostics["policy_event_mode"]), 1)
        self.assertEqual(int(diagnostics["policy_event_mask_fire_once"]), 1)
        self.assertEqual(int(diagnostics["policy_weapon_select_mode"]), 1)
        self.assertGreater(
            diagnostics["policy_weapon_select_station1_prob"],
            diagnostics["policy_weapon_select_station0_prob"],
        )

    def test_a5_event_info_columns_copy_runtime_event_contract_fields(self) -> None:
        columns = probe._a5_event_info_columns(
            {
                "engagement_state": "FiredAssess",
                "fire_mask": 0,
                "event_action_mask": [1, 0],
                "fire_once_requested": True,
                "fire_once_accepted": False,
                "fire_once_rejected_reason": "pending_assessment",
                "release_executed": False,
                "post_launch_suppressed": True,
                "reattack_ready": False,
                "fire_mask_components": {
                    "fire_mask_c2_authorized": 1,
                    "fire_mask_not_pending_assessment": 0,
                },
            }
        )

        self.assertEqual(columns["engagement_state"], "FiredAssess")
        self.assertEqual(columns["fire_mask"], 0)
        self.assertEqual(columns["event_action_mask_json"], "[1,0]")
        self.assertEqual(columns["event_action_mask_hold"], 1)
        self.assertEqual(columns["event_action_mask_fire_once"], 0)
        self.assertEqual(columns["fire_once_requested"], 1)
        self.assertEqual(columns["fire_once_accepted"], 0)
        self.assertEqual(columns["fire_once_rejected"], 1)
        self.assertEqual(columns["fire_once_rejected_reason"], "pending_assessment")
        self.assertEqual(columns["post_launch_suppressed"], 1)
        self.assertEqual(
            columns["fire_mask_components_json"],
            '{"fire_mask_c2_authorized":1,"fire_mask_not_pending_assessment":0}',
        )
        self.assertEqual(columns["fire_mask_c2_authorized"], 1)
        self.assertEqual(columns["fire_mask_not_pending_assessment"], 0)

    def test_lethality_chain_rows_project_effect_and_damage_into_standard_stages(self) -> None:
        rows = probe._lethality_chain_rows(
            episode=7,
            step=12,
            sim_time_s=4.5,
            engagement_events=_dummy_lethality_events(),
        )

        self.assertEqual([row["stage"] for row in rows], list(probe.LETHALITY_CHAIN_STAGES))
        for row in rows:
            for field in probe.LETHALITY_CHAIN_ROW_FIELDS:
                self.assertIn(field, row)
            self.assertFalse(any(str(key).startswith("last_effect_") for key in row))
            self.assertFalse(any(str(key).startswith("last_damage_") for key in row))
            self.assertEqual(row["schema_version"], 1)
            self.assertEqual(row["chain_id"], 301)
            self.assertEqual(row["munition_id"], 501)
            self.assertEqual(row["target_id"], 200)
            self.assertEqual(row["status"], "projected")

        nearest = next(row for row in rows if row["stage"] == "nearest_approach")
        self.assertAlmostEqual(nearest["miss_distance_m"], 12.5, places=6)
        self.assertAlmostEqual(nearest["local_forward_m"], 1.0, places=6)
        self.assertEqual(nearest["source_event_kind"], "EffectsEvent")
        self.assertEqual(nearest["source_event_id"], 101)

        fuze = next(row for row in rows if row["stage"] == "fuze")
        self.assertEqual(fuze["fuze_type"], "proximity")
        self.assertEqual(fuze["direct_hitbox_intersection"], 1)

        warhead = next(row for row in rows if row["stage"] == "warhead_mechanism")
        self.assertEqual(warhead["source_event_kind"], "EffectsEvent")
        self.assertEqual(warhead["mechanism_family"], "blast_fragmentation")
        self.assertAlmostEqual(warhead["fragment_energy_j"], 540.0, places=6)
        self.assertAlmostEqual(warhead["blast_overpressure_kpa"], 18.0, places=6)

        spatial = next(row for row in rows if row["stage"] == "spatial_coverage")
        self.assertEqual(spatial["source_event_kind"], "EffectsEvent")
        self.assertEqual(spatial["projected_hitbox_count"], 3)
        self.assertEqual(spatial["spatial_sample_count"], 240)

        platform = next(row for row in rows if row["stage"] == "platform_consequence")
        self.assertEqual(platform["parent_event_id"], 101)
        self.assertEqual(platform["damage_report_id"], 201)
        self.assertAlmostEqual(platform["system_health_delta"], -0.35, places=6)
        self.assertEqual(platform["mission_kill"], 1)
        self.assertEqual(platform["sensor_kill"], 1)

        lifecycle = next(row for row in rows if row["stage"] == "lifecycle")
        self.assertEqual(lifecycle["loss_state"], "lost")
        self.assertEqual(lifecycle["destroyed"], 1)

    def test_lethality_chain_rows_use_standard_geometry_and_fuze_events_without_effects(self) -> None:
        rows = probe._lethality_chain_rows(
            episode=7,
            step=12,
            sim_time_s=4.5,
            engagement_events=SimpleNamespace(
                nearest_approach_events=[_standard_nearest_event()],
                fuze_evaluation_events=[_standard_fuze_event()],
                effects_events=[],
                damage_reports=[],
                diagnostics_traces=[],
            ),
        )

        self.assertEqual([row["stage"] for row in rows], ["nearest_approach", "fuze"])
        for row in rows:
            for field in probe.LETHALITY_CHAIN_ROW_FIELDS:
                self.assertIn(field, row)
            self.assertFalse(any(str(key).startswith("last_effect_") for key in row))
            self.assertEqual(row["chain_id"], 301)
            self.assertEqual(row["munition_id"], 501)
            self.assertEqual(row["target_id"], 200)
            self.assertEqual(row["evidence_level"], "observed_runtime")

        nearest = rows[0]
        self.assertEqual(nearest["source_event_kind"], "NearestApproachEvent")
        self.assertEqual(nearest["source_event_id"], 102)
        self.assertEqual(nearest["status"], "observed")
        self.assertEqual(nearest["reason"], "fuze_no_detonation")
        self.assertAlmostEqual(nearest["miss_distance_m"], 12.5, places=6)
        self.assertAlmostEqual(nearest["closure_mps"], 725.0, places=6)
        self.assertEqual(nearest["aspect_bucket"], "beam")

        fuze = rows[1]
        self.assertEqual(fuze["source_event_kind"], "FuzeEvaluationEvent")
        self.assertEqual(fuze["source_event_id"], 103)
        self.assertEqual(fuze["parent_event_id"], 102)
        self.assertEqual(fuze["status"], "evaluated")
        self.assertEqual(fuze["reason"], "fuze_no_detonation")
        self.assertEqual(fuze["fuze_type"], "radar_proximity")
        self.assertEqual(fuze["fuze_armed"], 1)
        self.assertEqual(fuze["fuze_triggered"], 0)
        self.assertEqual(fuze["fuze_failure_reason"], "fuze_no_detonation")
        self.assertAlmostEqual(fuze["fuze_reliability"], 0.0, places=6)
        self.assertAlmostEqual(fuze["fuze_sample"], 0.42, places=6)
        self.assertAlmostEqual(fuze["fuze_trigger_radius_m"], 35.0, places=6)

        snapshot = probe._lethality_chain_snapshot_columns(rows)
        self.assertAlmostEqual(snapshot["lethality_chain_closure_mps"], 725.0, places=6)
        self.assertEqual(snapshot["lethality_chain_aspect_bucket"], "beam")
        self.assertEqual(snapshot["lethality_chain_fuze_armed"], 1)
        self.assertEqual(snapshot["lethality_chain_fuze_triggered"], 0)
        self.assertEqual(snapshot["lethality_chain_fuze_failure_reason"], "fuze_no_detonation")

    def test_standard_geometry_and_fuze_events_suppress_effects_fallback_rows(self) -> None:
        events = _dummy_lethality_events()
        events.nearest_approach_events = [_standard_nearest_event(reason="fuze_armed")]
        events.fuze_evaluation_events = [_standard_fuze_event(reason="fuze_armed", triggered=True)]

        rows = probe._lethality_chain_rows(
            episode=7,
            step=12,
            sim_time_s=4.5,
            engagement_events=events,
        )

        self.assertEqual([row["stage"] for row in rows], list(probe.LETHALITY_CHAIN_STAGES))
        nearest_rows = [row for row in rows if row["stage"] == "nearest_approach"]
        fuze_rows = [row for row in rows if row["stage"] == "fuze"]
        self.assertEqual(len(nearest_rows), 1)
        self.assertEqual(nearest_rows[0]["source_event_kind"], "NearestApproachEvent")
        self.assertEqual(nearest_rows[0]["reason"], "fuze_armed")
        self.assertEqual(len(fuze_rows), 1)
        self.assertEqual(fuze_rows[0]["source_event_kind"], "FuzeEvaluationEvent")
        self.assertEqual(fuze_rows[0]["fuze_triggered"], 1)
        self.assertEqual(fuze_rows[0]["fuze_failure_reason"], "")

    def test_standard_warhead_spatial_and_component_events_suppress_effects_fallback_rows(self) -> None:
        events = _dummy_lethality_events()
        events.warhead_mechanism_events = [_standard_warhead_event()]
        events.spatial_coverage_events = [_standard_spatial_event()]
        events.component_load_events = [_standard_component_load_event()]

        rows = probe._lethality_chain_rows(
            episode=7,
            step=12,
            sim_time_s=4.5,
            engagement_events=events,
        )

        warhead_rows = [row for row in rows if row["stage"] == "warhead_mechanism"]
        spatial_rows = [row for row in rows if row["stage"] == "spatial_coverage"]
        component_rows = [row for row in rows if row["stage"] == "component_load"]
        self.assertEqual(len(warhead_rows), 1)
        self.assertEqual(len(spatial_rows), 1)
        self.assertEqual(len(component_rows), 1)
        self.assertEqual(warhead_rows[0]["source_event_kind"], "WarheadMechanismEvent")
        self.assertEqual(warhead_rows[0]["source_event_id"], 104)
        self.assertEqual(warhead_rows[0]["reason"], "generic_research_warhead_profile")
        self.assertEqual(warhead_rows[0]["mechanism_family"], "blast_fragmentation")
        self.assertAlmostEqual(warhead_rows[0]["fragment_density_per_m2"], 17.0, places=6)
        self.assertEqual(spatial_rows[0]["source_event_kind"], "SpatialCoverageEvent")
        self.assertEqual(spatial_rows[0]["projected_hitbox_count"], 4)
        self.assertEqual(spatial_rows[0]["spatial_sample_count"], 360)
        self.assertEqual(component_rows[0]["source_event_kind"], "ComponentLoadEvent")
        self.assertEqual(component_rows[0]["component_hit_count"], 1)
        self.assertEqual(component_rows[0]["component_name"], "right_aileron_actuator")
        self.assertEqual(component_rows[0]["component_system"], "flight_control")
        self.assertEqual(component_rows[0]["component_load_source"], "direct_component_hit")

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

    def test_build_env_applies_multi_timescale_wrapper_from_train_config(self) -> None:
        class DummyEnv:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs
                self.unwrapped = self

        class DummyWrapper:
            def __init__(self, env, **kwargs):
                self.env = env
                self.kwargs = kwargs
                self.unwrapped = env.unwrapped

        old_env = probe.UniversalEnv
        old_wrapper = probe.MultiTimescaleActionWrapper
        old_get_spec = probe.get_action_wrapper_spec
        try:
            probe.UniversalEnv = DummyEnv
            probe.MultiTimescaleActionWrapper = DummyWrapper
            probe.get_action_wrapper_spec = lambda _cfg: (DummyWrapper, {"scripted_blend_indices": [0, 1, 2, 3]})

            env = probe._build_env(
                "scenarios/air_combat/1v1/dummy.json",
                {"env": {"action_mode": "air_combat_hybrid_v1"}},
            )

            self.assertIsInstance(env, DummyWrapper)
            self.assertEqual(env.kwargs["scripted_blend_indices"], [0, 1, 2, 3])
            self.assertIs(probe._base_env(env), env.env)
            self.assertEqual(env.env.kwargs["action_mode"], "air_combat_hybrid_v1")
        finally:
            probe.UniversalEnv = old_env
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

    def test_episode_summary_reports_authorized_window_policy_diagnostics(self) -> None:
        def row(
            step: int,
            *,
            auth: int = 1,
            pending: int = 0,
            shot_budget: int = 1,
            fire_prob: float = 0.2,
            fire_logit: float = -1.0,
        ) -> dict:
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
                "missiles_remaining": 4,
                "missile_release": 0,
                "missile_release_delta": 0,
                "action_radar_on": 1,
                "action_master_arm_on": 1,
                "action_fire_weapon_on": 0,
                "action_radar_active": 1.0,
                "action_master_arm": 1.0,
                "action_fire_weapon": 0.0,
                "effective_action_fire_weapon": 0.0,
                "authorization_to_fire": auth,
                "shot_budget_remaining": shot_budget,
                "pending_assessment": pending,
                "c2_roe_hold_fire": 0,
                "c2_roe_hold_fire_obeyed": 0,
                "c2_roe_hold_fire_violation": 0,
                "c2_roe_unauthorized_release_count": 0,
                "c2_roe_authorized_release_count": 0,
                "c2_roe_valid_authorized_release_count": 0,
                "c2_roe_violation_release_count": 0,
                "c2_roe_pending_assessment_release_count": 0,
                "c2_roe_premature_second_shot": 0,
                "c2_roe_shot_budget_violation": 0,
                "c2_roe_authorized_salvo_release_count": 0,
                "c2_roe_authorized_reattack_release_count": 0,
                "c2_roe_legacy_fallback_release_count": 0,
                "policy_prob_tms_up": 0.4,
                "policy_logit_tms_up": -0.25,
                "policy_prob_fire_weapon": fire_prob,
                "policy_logit_fire_weapon": fire_logit,
                "effects_event_count": 0,
                "damage_report_count": 0,
            }

        summary = probe._summarize_episode(
            [
                row(0, auth=0),
                row(1, fire_prob=0.25, fire_logit=-0.8),
                row(2, fire_prob=0.55, fire_logit=0.2),
                row(3, pending=1, shot_budget=0, fire_prob=0.9, fire_logit=1.2),
            ]
        )

        self.assertEqual(summary["authorized_window_step_count"], 2)
        self.assertAlmostEqual(summary["policy_prob_fire_weapon_max"], 0.9, places=6)
        self.assertAlmostEqual(summary["authorized_window_policy_prob_fire_weapon_mean"], 0.4, places=6)
        self.assertAlmostEqual(summary["authorized_window_policy_prob_fire_weapon_max"], 0.55, places=6)
        self.assertAlmostEqual(summary["authorized_window_policy_logit_fire_weapon_max"], 0.2, places=6)

    def test_episode_summary_reports_a5_event_action_counts(self) -> None:
        def row(
            step: int,
            *,
            state: str = "Hold",
            mask: int = 0,
            requested: int = 0,
            accepted: int = 0,
            executed: int = 0,
            suppressed: int = 0,
            reason: str = "",
            event_prob: float = 0.0,
            event_mode: int = 0,
        ) -> dict:
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
                "missiles_remaining": 4 - executed,
                "missile_release": executed,
                "missile_release_delta": executed,
                "action_radar_on": 1,
                "action_master_arm_on": 1,
                "action_fire_weapon_on": requested,
                "action_radar_active": 1.0,
                "action_master_arm": 1.0,
                "action_fire_weapon": float(requested),
                "effective_action_fire_weapon": float(accepted),
                "authorization_to_fire": int(mask),
                "shot_budget_remaining": 1,
                "pending_assessment": int(state == "FiredAssess"),
                "engagement_state": state,
                "fire_mask": mask,
                "fire_once_requested": requested,
                "fire_once_accepted": accepted,
                "fire_once_rejected": int(requested and not accepted),
                "fire_once_rejected_reason": reason,
                "release_executed": executed,
                "post_launch_suppressed": suppressed,
                "policy_event_prob_fire_once": event_prob,
                "policy_event_logit_fire_once": event_prob,
                "policy_event_mode": event_mode,
                "policy_event_mask_fire_once": mask,
                "effects_event_count": 0,
                "damage_report_count": 0,
            }

        summary = probe._summarize_episode(
            [
                row(0),
                row(1, state="AuthorizedReady", mask=1, requested=1, accepted=1, executed=1, event_prob=0.8, event_mode=1),
                row(2, state="FiredAssess", requested=1, reason="pending_assessment", suppressed=1, event_prob=0.0),
                row(3, state="FiredAssess"),
            ]
        )

        self.assertEqual(summary["fire_mask_open_step_count"], 1)
        self.assertEqual(summary["fire_once_requested_count"], 2)
        self.assertEqual(summary["fire_once_accepted_count"], 1)
        self.assertEqual(summary["fire_once_rejected_count"], 1)
        self.assertEqual(summary["release_executed_count"], 1)
        self.assertEqual(summary["post_launch_suppressed_count"], 1)
        self.assertEqual(summary["fire_once_rejected_reason_counts"], {"pending_assessment": 1})
        self.assertEqual(summary["engagement_state_counts"], {"AuthorizedReady": 1, "FiredAssess": 2})
        self.assertEqual(summary["policy_event_mode_fire_once_count"], 1)
        self.assertEqual(summary["policy_event_mask_fire_once_open_count"], 1)

    def test_c2_roe_event_columns_split_authorized_salvo_and_budget_violation(self) -> None:
        state = {
            "contract_present": True,
            "roe_state": 2,
            "wcs_state": 2,
            "authorization_to_fire": True,
            "engage_order_state": 2,
            "shot_policy_state": 2,
            "shot_budget_remaining": 1,
            "pending_assessment": False,
        }

        columns = probe._c2_roe_event_columns(
            state,
            release_delta=2,
            fire_attempted=True,
            previous_release_count=0,
        )

        self.assertEqual(columns["c2_roe_release_bucket"], "authorized_salvo")
        self.assertEqual(columns["c2_roe_authorized_release_count"], 1)
        self.assertEqual(columns["c2_roe_authorized_salvo_release_count"], 1)
        self.assertEqual(columns["c2_roe_shot_budget_violation"], 1)
        self.assertEqual(columns["c2_roe_violation_release_count"], 1)

    def test_episode_summary_reports_c2_roe_release_discipline_buckets(self) -> None:
        def row(
            step: int,
            *,
            fire: int = 0,
            release_delta: int = 0,
            auth: int = 1,
            wcs: int = 2,
            pending: int = 0,
            authorized: int = 0,
            violation: int = 0,
            unauthorized: int = 0,
            pending_release: int = 0,
            salvo: int = 0,
            reattack: int = 0,
            hold_violation: int = 0,
        ) -> dict:
            return {
                "episode": 0,
                "step": step,
                "reward": 0.0,
                "terminated": int(step == 4),
                "truncated": 0,
                "termination_reason": "combat_timeout" if step == 4 else "",
                "target_range_geom_m": 12000.0 - step,
                "target_health": 100.0,
                "can_fire": 1,
                "target_contact": 1,
                "target_active": 1,
                "missiles_remaining": 4 - release_delta,
                "missile_release": int(release_delta > 0),
                "missile_release_delta": release_delta,
                "action_radar_on": 1,
                "action_master_arm_on": 1,
                "action_fire_weapon_on": fire,
                "action_radar_active": 1.0,
                "action_master_arm": 1.0,
                "action_fire_weapon": float(fire),
                "effective_action_fire_weapon": float(fire),
                "roe_state": 2,
                "wcs_state": wcs,
                "authorization_to_fire": auth,
                "pending_assessment": pending,
                "c2_roe_hold_fire": int(wcs == 1),
                "c2_roe_hold_fire_obeyed": 0,
                "c2_roe_hold_fire_violation": hold_violation,
                "c2_roe_unauthorized_release_count": unauthorized,
                "c2_roe_authorized_release_count": authorized,
                "c2_roe_valid_authorized_release_count": authorized,
                "c2_roe_violation_release_count": violation,
                "c2_roe_pending_assessment_release_count": pending_release,
                "c2_roe_premature_second_shot": 0,
                "c2_roe_shot_budget_violation": 0,
                "c2_roe_authorized_salvo_release_count": salvo,
                "c2_roe_authorized_reattack_release_count": reattack,
                "c2_roe_legacy_fallback_release_count": 0,
                "effects_event_count": 0,
                "damage_report_count": 0,
            }

        summary = probe._summarize_episode(
            [
                row(0, fire=0, auth=0, wcs=1),
                row(1, fire=1, release_delta=1, authorized=1, salvo=1),
                row(2, fire=0),
                row(3, fire=1, release_delta=1, auth=1, pending=1, violation=1, pending_release=1),
                row(4, fire=1, release_delta=1, auth=0, wcs=1, violation=1, unauthorized=1, hold_violation=1),
            ]
        )

        self.assertEqual(summary["authorized_release_count"], 1)
        self.assertEqual(summary["unauthorized_release_count"], 1)
        self.assertEqual(summary["violation_release_count"], 2)
        self.assertEqual(summary["pending_assessment_release_count"], 1)
        self.assertEqual(summary["authorized_salvo_release_count"], 1)
        self.assertEqual(summary["authorized_reattack_release_count"], 0)
        self.assertEqual(summary["fire_under_hold_count"], 1)
        self.assertEqual(summary["release_count_by_authorization_state"]["authorized"], 1)
        self.assertEqual(summary["release_count_by_authorization_state"]["unauthorized"], 1)
        self.assertEqual(summary["release_count_by_authorization_state"]["violation"], 2)
        self.assertEqual(summary["roe_state_at_fire"], [2, 2])
        self.assertEqual(summary["authorization_to_fire_at_fire"], [1, 1])

    def test_legal_mask_fire_action_waits_for_open_mask_delay_and_one_shot(self) -> None:
        old_open = probe._legal_fire_mask_open
        try:
            probe._legal_fire_mask_open = lambda *args, **kwargs: True

            action, fired, age = probe._legal_mask_fire_action(
                env=object(),
                action_mode="air_combat_hybrid_v1",
                already_fired=False,
                legal_open_age_steps=30,
                fire_delay_steps=31,
            )

            self.assertFalse(fired)
            self.assertEqual(age, 31)
            self.assertEqual(float(action[9]), 0.0)

            action, fired, age = probe._legal_mask_fire_action(
                env=object(),
                action_mode="air_combat_hybrid_v1",
                already_fired=False,
                legal_open_age_steps=31,
                fire_delay_steps=31,
            )

            self.assertTrue(fired)
            self.assertEqual(age, 32)
            self.assertEqual(float(action[9]), 1.0)

            action, fired, age = probe._legal_mask_fire_action(
                env=object(),
                action_mode="air_combat_hybrid_v1",
                already_fired=True,
                legal_open_age_steps=32,
                fire_delay_steps=31,
            )

            self.assertFalse(fired)
            self.assertEqual(age, 33)
            self.assertEqual(float(action[9]), 0.0)
        finally:
            probe._legal_fire_mask_open = old_open

    def test_legal_mask_fire_action_resets_age_when_mask_closes(self) -> None:
        old_open = probe._legal_fire_mask_open
        try:
            probe._legal_fire_mask_open = lambda *args, **kwargs: False

            action, fired, age = probe._legal_mask_fire_action(
                env=object(),
                action_mode="air_combat_hybrid_v1",
                already_fired=False,
                legal_open_age_steps=12,
                fire_delay_steps=0,
            )

            self.assertFalse(fired)
            self.assertEqual(age, 0)
            self.assertEqual(float(action[9]), 0.0)
        finally:
            probe._legal_fire_mask_open = old_open


if __name__ == "__main__":
    unittest.main()
