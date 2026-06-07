from __future__ import annotations

from .helpers import *


_A8_MQ9_AIM120_INTEGRATION_FOLLOWUPS = (
    "A8-W1 shot-effect record fields for staged fuze/warhead/part/consequence assertions",
    "A8-W2 concrete damage-mode vocabulary for cut/leak/data-loss/power-loss assertions",
    "A8-DEC-E consumer checks for sustained post-hit aerodynamic response",
)


def _spawn_f16_mq9_pair(
    sim: ef_py.SimulationKernel,
    *,
    range_m: float,
    altitude_m: float = 5000.0,
    target_speed_mps: float = 120.0,
) -> tuple[int, int]:
    shooter_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            0.0,
            0.0,
            altitude_m,
            0.0,
            0.0,
            0.0,
            0.0,
            250.0,
            0.0,
        )
    )
    target_id = int(
        sim.spawn_unit(
            ef_py.Side.Red,
            "MQ-9_Reaper",
            0.0,
            range_m,
            altitude_m,
            180.0,
            0.0,
            0.0,
            0.0,
            -float(target_speed_mps),
            0.0,
        )
    )
    sim.set_unit_ammo(shooter_id, 4, 4)
    sim.set_weapon_cooldown(shooter_id, 0.0, -1.0)
    pilot = ef_py.PilotAction()
    pilot.active = True
    pilot.weapon_select_id = 1
    sim.set_pilot_action(shooter_id, pilot)
    _set_contacts(
        sim,
        shooter_id,
        [
            _relative_detection_from_truth(
                sim,
                shooter_id,
                target_id,
                timestamp=0.0,
                local_sensor_hit=True,
            )
        ],
    )
    return shooter_id, target_id


def _launch_and_drive_mq9_case(
    *,
    range_m: float,
    max_steps: int = 3600,
) -> tuple[ef_py.SimulationKernel, int, int, int, dict[str, float | bool], dict]:
    sim = ef_py.SimulationKernel()
    sim.reset(20260607)
    if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")
    sim.set_time_step(1.0 / 60.0)
    shooter_id, target_id = _spawn_f16_mq9_pair(sim, range_m=range_m)
    missile_id = int(sim.fire_missile(shooter_id, target_id))
    if missile_id <= 0:
        raise AssertionError(f"expected AIM-120C launch against MQ-9 at {range_m} m")
    missile_runtime = _missile_runtime(sim, missile_id)
    result = _drive_missile_with_truth_track(
        sim,
        missile_id,
        target_id,
        max_steps=max_steps,
    )
    return sim, shooter_id, target_id, missile_id, result, missile_runtime


def _profiled_mq9_aim120_hit(
    local: tuple[float, float, float],
    *,
    damage: float = 120.0,
    radius: float = 35.0,
    velocity: tuple[float, float, float] = (900.0, -250.0, 0.0),
) -> tuple[dict[str, float], dict[str, float], object, object]:
    sim = _kernel_with_unit_overrides([])
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")
    before = _aircraft_damage_overlay(sim, target_id)
    ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id,
        target_id,
        float(local[0]),
        float(local[1]),
        float(local[2]),
        _make_warhead_profile("blast_fragmentation", damage=damage, radius=radius),
        float(velocity[0]),
        float(velocity[1]),
        float(velocity[2]),
    )
    if not ok:
        raise AssertionError("profiled MQ-9/AIM-120C local hit failed")
    events = sim.export_recent_engagement_events()
    if len(events.effects_events) != 1:
        raise AssertionError("expected one MQ-9/AIM-120C effects event")
    if len(events.damage_reports) != 1:
        raise AssertionError("expected one MQ-9/AIM-120C damage report")
    return (
        before,
        _aircraft_damage_overlay(sim, target_id),
        events.effects_events[0],
        events.damage_reports[0],
    )


def _assert_mq9_event_is_non_authoritative(testcase: unittest.TestCase, event: object) -> None:
    testcase.assertTrue(bool(event.vulnerability_profile_present))
    testcase.assertTrue(bool(event.vulnerability_profile_synthetic))
    testcase.assertFalse(bool(event.vulnerability_calibrated_evidence))
    testcase.assertFalse(bool(event.vulnerability_pk_authority))
    testcase.assertFalse(bool(event.vulnerability_deterministic_fuze_authority))
    testcase.assertEqual(str(event.vulnerability_calibration_status), "unvalidated")
    testcase.assertEqual(str(event.component_failure_probability_source), "synthetic_sigmoid")
    testcase.assertFalse(bool(event.component_failure_probability_calibrated))


def _component_rows_by_name(event: object) -> dict[str, object]:
    return {str(row.component_name): row for row in event.component_mechanism_load_rows}


class A8Mq9Aim120ValidationRuntimeMixin:
    def test_a8_mq9_aim120_near_range_live_chain_records_launch_effect_damage(
        self,
    ) -> None:
        sim, _shooter_id, target_id, missile_id, result, missile_runtime = (
            _launch_and_drive_mq9_case(range_m=8000.0)
        )

        self.assertFalse(bool(result["missile_active"]))
        self.assertTrue(bool(result["target_active"]))
        self.assertTrue(sim.is_unit_active(target_id))
        self.assertLessEqual(float(result["proximity_min_dist_m"]), 15.0)
        self.assertAlmostEqual(
            float(missile_runtime["mass_total_kg"]),
            152.0,
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(missile_runtime["max_speed_mps"]),
            1372.0,
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(missile_runtime["seeker_lock_range_m"]),
            16000.0,
            delta=1.0e-6,
        )
        self.assertEqual(int(missile_runtime["sensor_type"]), int(ef_py.SensorType.Radar))

        events = sim.export_recent_engagement_events()
        self.assertEqual(len(events.launch_events), 1)
        self.assertEqual(len(events.effects_events), 1)
        self.assertEqual(len(events.damage_reports), 1)
        effect = events.effects_events[0]
        report = events.damage_reports[0]

        self.assertEqual(int(effect.munition.entity_id), missile_id)
        self.assertEqual(int(effect.target.entity_id), target_id)
        self.assertEqual(str(effect.trigger_type), "proximity_fuze")
        self.assertEqual(str(effect.fuze_type), "radar_proximity")
        self.assertEqual(str(effect.effect_family), "blast_fragmentation")
        self.assertEqual(str(effect.component_primary_name), "right_aileron_servo")
        self.assertEqual(str(effect.component_primary_system), "flight_control")
        self.assertGreaterEqual(int(effect.component_hit_count), 1)
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertFalse(bool(report.destroyed))
        self.assertEqual(str(report.loss_state_to), "combat_capable")
        _assert_mq9_event_is_non_authoritative(self, effect)

        overlay = _aircraft_damage_overlay(sim, target_id)
        self.assertLess(overlay["flight_control"], 1.0)
        self.assertLess(overlay["roll_control"], 1.0)
        self.assertLess(overlay["propulsion"], 1.0)
        self.assertLess(overlay["fuel"], 1.0)
        self.assertGreater(overlay["fuel_leak"], 0.0)

    def test_a8_mq9_aim120_longer_range_live_chain_is_auditable_without_lethality_claim(
        self,
    ) -> None:
        sim, _shooter_id, target_id, _missile_id, result, missile_runtime = (
            _launch_and_drive_mq9_case(range_m=14000.0)
        )

        self.assertFalse(bool(result["missile_active"]))
        self.assertTrue(bool(result["target_active"]))
        self.assertGreater(float(result["time_s"]), 8.0)
        self.assertLessEqual(float(result["proximity_min_dist_m"]), 15.0)
        self.assertAlmostEqual(
            float(missile_runtime["max_flight_time_s"]),
            45.0,
            delta=1.0e-6,
        )

        events = sim.export_recent_engagement_events()
        self.assertEqual(len(events.launch_events), 1)
        self.assertEqual(len(events.effects_events), 1)
        self.assertEqual(len(events.damage_reports), 1)
        effect = events.effects_events[0]
        report = events.damage_reports[0]

        self.assertEqual(str(effect.trigger_type), "proximity_fuze")
        self.assertEqual(str(effect.effect_family), "blast_fragmentation")
        self.assertGreaterEqual(int(effect.component_hit_count), 1)
        self.assertNotEqual(str(effect.component_primary_name), "")
        self.assertGreater(float(effect.miss_distance_m), 0.0)
        self.assertLessEqual(float(effect.miss_distance_m), 15.0)
        self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
        self.assertLess(float(report.system_health_delta), 0.0)
        self.assertFalse(bool(report.destroyed))
        self.assertTrue(sim.is_unit_active(target_id))
        _assert_mq9_event_is_non_authoritative(self, effect)

        health_after = [float(value) for value in sim.get_unit_health(target_id)]
        self.assertEqual(health_after, [40.0, 40.0])
        overlay = _aircraft_damage_overlay(sim, target_id)
        self.assertLess(
            min(
                overlay["flight_control"],
                overlay["propulsion"],
                overlay["fuel"],
                overlay["avionics"],
            ),
            1.0,
        )

    def test_a8_mq9_aim120_right_aileron_and_flap_control_hits_are_fixed_component_cases(
        self,
    ) -> None:
        cases = [
            {
                "label": "right_aileron",
                "local": (-0.4, 8.0, 0.0),
                "component": "right_aileron_servo",
                "drops": ("flight_control", "roll_control"),
                "stable": ("pitch_control", "yaw_control"),
                "rises": ("control_asymmetry",),
            },
            {
                "label": "right_flap",
                "local": (-0.2, 2.8, 0.0),
                "component": "right_inboard_flap_servo",
                "drops": ("flight_control", "roll_control", "pitch_control"),
                "stable": ("yaw_control",),
                "rises": ("control_asymmetry",),
            },
        ]

        for case in cases:
            with self.subTest(case=case["label"]):
                before, after, effect, report = _profiled_mq9_aim120_hit(case["local"])
                self.assertTrue(bool(effect.direct_hitbox_intersection))
                self.assertEqual(str(effect.component_primary_name), case["component"])
                self.assertEqual(str(effect.component_primary_system), "flight_control")
                self.assertIn(case["component"], _component_rows_by_name(effect))
                self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
                self.assertFalse(bool(report.destroyed))
                _assert_mq9_event_is_non_authoritative(self, effect)

                for field in case["drops"]:
                    self.assertLess(after[field], before[field], field)
                for field in case["stable"]:
                    self.assertAlmostEqual(after[field], before[field], delta=1.0e-6, msg=field)
                for field in case["rises"]:
                    self.assertGreater(after[field], before[field], field)

    def test_a8_mq9_aim120_data_link_and_power_distribution_hits_degrade_mission_path_without_crash(
        self,
    ) -> None:
        cases = [
            {
                "label": "data_link",
                "local": (1.0, 0.0, 0.2),
                "component": "data_link_transceiver",
                "system": "data_link",
                "drops": ("avionics", "mission_crew", "command_navigation"),
            },
            {
                "label": "power_distribution",
                "local": (-1.8, 0.0, 0.2),
                "component": "power_distribution_unit",
                "system": "avionics",
                "drops": ("avionics", "flight_control", "command_navigation"),
            },
        ]

        for case in cases:
            with self.subTest(case=case["label"]):
                before, after, effect, report = _profiled_mq9_aim120_hit(case["local"])
                self.assertTrue(bool(effect.direct_hitbox_intersection))
                self.assertEqual(str(effect.component_primary_name), case["component"])
                self.assertEqual(str(effect.component_primary_system), case["system"])
                self.assertGreaterEqual(int(effect.component_hit_count), 1)
                self.assertAlmostEqual(float(report.hp_delta), 0.0, delta=1.0e-6)
                self.assertLess(float(report.system_health_delta), 0.0)
                self.assertFalse(bool(report.destroyed))
                self.assertNotEqual(str(report.loss_state_to), "lost")
                _assert_mq9_event_is_non_authoritative(self, effect)

                for field in case["drops"]:
                    self.assertLess(after[field], before[field], field)

    def test_a8_mq9_aim120_explicit_non_authority_guard_for_fixture_and_events(
        self,
    ) -> None:
        with open(
            resolve_repo_path(
                "examples",
                "config",
                "database",
                "aircraft",
                "units",
                "mq9_reaper.json",
            ),
            "r",
            encoding="utf-8",
        ) as handle:
            mq9 = json.load(handle)
        vulnerability = mq9["damage_model"]["vulnerability"]
        self.assertTrue(bool(vulnerability["synthetic"]))
        self.assertFalse(bool(vulnerability["calibrated"]))
        self.assertFalse(bool(vulnerability["pk_authority"]))
        self.assertFalse(bool(vulnerability["deterministic_fuze_authority"]))
        self.assertEqual(str(vulnerability["calibration_status"]), "unvalidated")

        sim = _kernel_with_unit_overrides([])
        _attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")
        evidence = [
            float(value)
            for value in sim.debug_get_aircraft_vulnerability_evidence_state(target_id)
        ]
        authority = [
            float(value)
            for value in sim.debug_get_aircraft_vulnerability_authority_state(target_id)
        ]
        self.assertEqual(evidence, [1.0, 1.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(authority, [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        _before, _after, effect, _report = _profiled_mq9_aim120_hit((-4.4, 0.0, 0.0))
        _assert_mq9_event_is_non_authoritative(self, effect)

    @unittest.skip(
        "A8-W1/W2 integration follow-up: requires public shot-effect record "
        "fields and concrete damage-mode vocabulary"
    )
    def test_a8_mq9_aim120_stage_record_contract_after_w1_w2_lands(self) -> None:
        self.assertEqual(
            _A8_MQ9_AIM120_INTEGRATION_FOLLOWUPS,
            (),
            "Remove this scaffold once W1/W2 expose authoritative test fields.",
        )
