from __future__ import annotations

from python.testing.runtime import configure_sim_log_level

from .a8_mq9_aim120 import _assert_mq9_event_is_non_authoritative
from .helpers import *


configure_sim_log_level("error")


def _neutral_f16_after_optional_right_aileron_damage(
    *,
    damaged: bool,
    steps: int = 60,
) -> tuple[object, dict[str, float], object | None]:
    sim = ef_py.SimulationKernel()
    sim.reset(20260608)
    if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")
    sim.set_time_step(1.0 / 60.0)
    attacker_id, target_id = _spawn_structured_f16_pair(sim)

    report = None
    if damaged:
        ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
            attacker_id,
            target_id,
            -0.8,
            4.1,
            0.0,
            _make_warhead_profile("blast_fragmentation", damage=75.0, radius=35.0),
            900.0,
            -250.0,
            0.0,
        )
        if not ok:
            raise AssertionError("profiled right-aileron hit failed")
        events = sim.export_recent_engagement_events()
        report = events.damage_reports[-1]

    for _ in range(int(steps)):
        sim.step()

    return sim.get_instrument_state(target_id), _aircraft_damage_overlay(sim, target_id), report


def _neutral_mq9_after_optional_right_aileron_damage(
    *,
    damaged: bool,
    steps: int = 60,
) -> tuple[object, dict[str, float], object | None, object | None, bool]:
    sim = _kernel_with_unit_overrides([])
    sim.set_time_step(1.0 / 60.0)
    attacker_id, target_id = _spawn_attacker_and_named_target(sim, "MQ-9_Reaper")

    effect = None
    report = None
    if damaged:
        ok = sim.debug_apply_profiled_local_proximity_hit_with_velocity(
            attacker_id,
            target_id,
            -0.4,
            8.0,
            0.0,
            _make_warhead_profile("blast_fragmentation", damage=120.0, radius=35.0),
            900.0,
            -250.0,
            0.0,
        )
        if not ok:
            raise AssertionError("profiled MQ-9 right-aileron hit failed")
        events = sim.export_recent_engagement_events()
        effect = events.effects_events[-1]
        report = events.damage_reports[-1]

    for _ in range(int(steps)):
        sim.step()

    return (
        sim.get_instrument_state(target_id),
        _aircraft_damage_overlay(sim, target_id),
        effect,
        report,
        bool(sim.is_unit_active(target_id)),
    )


class A8AeroConsumerRuntimeMixin:
    def test_a8_wing_control_damage_reaches_neutral_aero_response_without_kill_verdict(
        self,
    ) -> None:
        baseline_inst, baseline_overlay, _baseline_report = (
            _neutral_f16_after_optional_right_aileron_damage(damaged=False)
        )
        damaged_inst, damaged_overlay, damaged_report = (
            _neutral_f16_after_optional_right_aileron_damage(damaged=True)
        )

        self.assertIsNotNone(damaged_report)
        assert damaged_report is not None
        self.assertFalse(bool(damaged_report.destroyed))
        self.assertEqual(str(damaged_report.loss_state_to), "combat_capable")
        self.assertFalse(bool(damaged_report.forced_landing))
        self.assertLess(damaged_overlay["flight_control"], baseline_overlay["flight_control"])
        self.assertLess(damaged_overlay["roll_control"], baseline_overlay["roll_control"])
        self.assertGreater(damaged_overlay["control_asymmetry"], baseline_overlay["control_asymmetry"])

        roll_delta_deg = abs(float(damaged_inst.roll) - float(baseline_inst.roll))
        beta_delta_deg = abs(float(damaged_inst.beta) - float(baseline_inst.beta))
        self.assertGreater(roll_delta_deg, 5.0)
        self.assertGreater(beta_delta_deg, 2.0)

    def test_a8_mq9_aim120_right_aileron_damage_changes_roll_response_through_aero_path(
        self,
    ) -> None:
        baseline_inst, baseline_overlay, _baseline_effect, _baseline_report, baseline_active = (
            _neutral_mq9_after_optional_right_aileron_damage(damaged=False)
        )
        damaged_inst, damaged_overlay, damaged_effect, damaged_report, damaged_active = (
            _neutral_mq9_after_optional_right_aileron_damage(damaged=True)
        )

        self.assertTrue(baseline_active)
        self.assertTrue(damaged_active)
        self.assertIsNotNone(damaged_effect)
        self.assertIsNotNone(damaged_report)
        assert damaged_effect is not None
        assert damaged_report is not None

        self.assertEqual(str(damaged_effect.component_primary_name), "right_aileron_servo")
        self.assertEqual(str(damaged_effect.component_primary_system), "flight_control")
        self.assertAlmostEqual(float(damaged_report.hp_delta), 0.0, delta=1.0e-6)
        self.assertFalse(bool(damaged_report.destroyed))
        self.assertTrue(bool(damaged_effect.direct_hitbox_intersection))
        _assert_mq9_event_is_non_authoritative(self, damaged_effect)

        self.assertLess(damaged_overlay["flight_control"], baseline_overlay["flight_control"])
        self.assertLess(damaged_overlay["roll_control"], baseline_overlay["roll_control"])
        self.assertGreater(
            damaged_overlay["control_asymmetry"],
            baseline_overlay["control_asymmetry"],
        )

        roll_delta_deg = abs(float(damaged_inst.roll) - float(baseline_inst.roll))
        beta_delta_deg = abs(float(damaged_inst.beta) - float(baseline_inst.beta))
        speed_delta_mps = abs(
            float(damaged_inst.ground_speed) - float(baseline_inst.ground_speed)
        )
        self.assertGreater(roll_delta_deg, 5.0)
        self.assertGreater(beta_delta_deg, 2.0)
        self.assertGreater(speed_delta_mps, 2.0)
