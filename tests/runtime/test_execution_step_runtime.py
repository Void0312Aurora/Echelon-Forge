from __future__ import annotations

import math
import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


class ExecutionStepRuntimeTests(unittest.TestCase):
    def test_nan_guard_returns_early_failure_and_skips_other_paths(self) -> None:
        inputs = ef_py.ExecutionStepRuntimeInputs()
        inputs.safety.finite_state_valid = False
        inputs.safety.crash_penalty = -321.0
        inputs.has_approach = True
        inputs.approach.valid = True
        inputs.approach.capture_bonus = 5.0
        inputs.has_waypoint = True
        inputs.waypoint.valid = True
        inputs.waypoint.reached_bonus = 10.0
        inputs.has_objectives = True
        inputs.objectives = [ef_py.ConditionalObjectiveSpec()]

        out = ef_py.compute_execution_step_runtime(inputs)
        self.assertTrue(bool(out.valid))
        self.assertTrue(bool(out.terminated))
        self.assertEqual(out.reason_code, ef_py.TerminationReasonCode.NanGuard)
        self.assertEqual(out.final_reason_code, ef_py.TerminationReasonCode.NanGuard)
        self.assertAlmostEqual(float(out.compiled_reward_total), -321.0, places=6)
        self.assertFalse(bool(out.approach_evaluated))
        self.assertFalse(bool(out.waypoint_evaluated))
        self.assertFalse(bool(out.objective_evaluated))

    def test_waypoint_success_has_priority_over_objectives(self) -> None:
        inputs = ef_py.ExecutionStepRuntimeInputs()
        inputs.safety.finite_state_valid = True
        inputs.safety.health = 100.0
        inputs.safety.survival_reward = 0.02

        inputs.has_waypoint = True
        inputs.waypoint.valid = True
        inputs.waypoint.waypoint_index = 1
        inputs.waypoint.waypoint_count = 2
        inputs.waypoint.dist_m = 80.0
        inputs.waypoint.waypoint_radius_m = 100.0
        inputs.waypoint.reached_bonus = 7.0
        inputs.waypoint_episode_success = True
        inputs.waypoint_episode_success_bonus = 600.0

        spec = ef_py.ConditionalObjectiveSpec()
        spec.reward_bonus = 2200.0
        cond = ef_py.ConditionalObjectiveCondition()
        cond.property_code = ef_py.ConditionalObjectiveProperty.OnGround
        cond.op_code = ef_py.ConditionalObjectiveOp.GreaterEqual
        cond.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
        cond.target_value = 0.5
        spec.conditions = [cond]
        inputs.has_objectives = True
        inputs.objectives = [spec]
        inputs.objective_inputs.on_ground = True

        out = ef_py.compute_execution_step_runtime(inputs)
        self.assertTrue(bool(out.valid))
        self.assertTrue(bool(out.waypoint_evaluated))
        self.assertTrue(bool(out.waypoint.arrived))
        self.assertTrue(bool(out.waypoint_episode_success))
        self.assertTrue(bool(out.terminated))
        self.assertEqual(out.reason_code, ef_py.TerminationReasonCode.SuccessWaypoint)
        self.assertEqual(out.final_reason_code, ef_py.TerminationReasonCode.SuccessWaypoint)
        self.assertEqual(int(out.matched_objective_index), -1)
        self.assertAlmostEqual(float(out.compiled_reward_total), 607.02, places=6)

    def test_objective_match_updates_status_and_aggregates_shaping(self) -> None:
        inputs = ef_py.ExecutionStepRuntimeInputs()
        inputs.safety.finite_state_valid = True
        inputs.safety.health = 100.0
        inputs.safety.survival_reward = 0.02

        inputs.has_approach = True
        inputs.approach.valid = True
        inputs.approach.ils_valid = True
        inputs.approach.ils_loc_dev = 0.1
        inputs.approach.ils_gs_dev = 0.1
        inputs.approach.ils_dme_m = 9000.0
        inputs.approach.has_prev_loc = True
        inputs.approach.prev_loc_abs = 0.3
        inputs.approach.has_prev_gs = True
        inputs.approach.prev_gs_abs = 0.4
        inputs.approach.has_prev_dme = True
        inputs.approach.prev_dme_m = 9100.0
        inputs.approach.localizer_improve_weight = 2.0
        inputs.approach.glideslope_improve_weight = 2.0
        inputs.approach.dme_progress_weight = 1.0
        inputs.approach.dme_progress_localizer_band = 0.2
        inputs.approach.dme_progress_glideslope_band = 0.2
        inputs.approach.capture_bonus = 5.0
        inputs.approach.capture_localizer_band = 0.2
        inputs.approach.capture_glideslope_band = 0.2

        spec = ef_py.ConditionalObjectiveSpec()
        spec.reward_bonus = 2200.0

        cond_alt = ef_py.ConditionalObjectiveCondition()
        cond_alt.property_code = ef_py.ConditionalObjectiveProperty.AltitudeAGL
        cond_alt.op_code = ef_py.ConditionalObjectiveOp.LessEqual
        cond_alt.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
        cond_alt.target_value = 2.5

        cond_ground = ef_py.ConditionalObjectiveCondition()
        cond_ground.property_code = ef_py.ConditionalObjectiveProperty.OnGround
        cond_ground.op_code = ef_py.ConditionalObjectiveOp.GreaterEqual
        cond_ground.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
        cond_ground.target_value = 0.5

        cond_speed = ef_py.ConditionalObjectiveCondition()
        cond_speed.property_code = ef_py.ConditionalObjectiveProperty.Speed
        cond_speed.op_code = ef_py.ConditionalObjectiveOp.LessEqual
        cond_speed.target_kind = ef_py.ConditionalObjectiveTargetKind.CommandSpeed
        cond_speed.target_scale = 1.1

        spec.conditions = [cond_alt, cond_ground, cond_speed]
        inputs.has_objectives = True
        inputs.objectives = [spec]
        inputs.objective_inputs.altitude_agl_m = 1.5
        inputs.objective_inputs.on_ground = True
        inputs.objective_inputs.speed_mps = 95.0
        inputs.objective_inputs.target_speed_mps = 100.0
        inputs.objective_inputs.has_runway_cross_m = True
        inputs.objective_inputs.runway_cross_m = 6.0
        inputs.objective_inputs.ground_track_error_deg = 12.0

        inputs.objective_shaping.runway_cross_penalty_weight = -0.5
        inputs.objective_shaping.runway_cross_deadband_m = 2.0
        inputs.objective_shaping.runway_cross_norm_m = 10.0
        inputs.objective_shaping.runway_cross_power = 2.0
        inputs.objective_shaping.ground_track_penalty_weight = -1.0
        inputs.objective_shaping.ground_track_deadband_deg = 5.0
        inputs.objective_shaping.ground_track_norm_deg = 10.0
        inputs.objective_shaping.ground_track_power = 2.0

        out = ef_py.compute_execution_step_runtime(inputs)
        self.assertTrue(bool(out.valid))
        self.assertTrue(bool(out.approach_evaluated))
        self.assertTrue(bool(out.objective_evaluated))
        self.assertTrue(bool(out.terminated))
        self.assertEqual(out.reason_code, ef_py.TerminationReasonCode.SuccessObjective)
        self.assertEqual(out.final_reason_code, ef_py.TerminationReasonCode.SuccessObjective)
        self.assertEqual(int(out.matched_objective_index), 0)
        self.assertAlmostEqual(float(out.status0), 1.5, places=6)
        self.assertAlmostEqual(float(out.status1), 1.0, places=6)
        self.assertAlmostEqual(float(out.status2), 95.0, places=6)
        self.assertTrue(math.isclose(float(out.compiled_reward_total), 2230.45, rel_tol=1.0e-6, abs_tol=1.0e-6))

    def test_truncated_nonterminal_step_finalizes_to_timeout(self) -> None:
        inputs = ef_py.ExecutionStepRuntimeInputs()
        inputs.safety.finite_state_valid = True
        inputs.safety.health = 100.0
        inputs.safety.survival_reward = 0.02
        inputs.truncated = True

        out = ef_py.compute_execution_step_runtime(inputs)
        self.assertTrue(bool(out.valid))
        self.assertFalse(bool(out.terminated))
        self.assertEqual(out.reason_code, ef_py.TerminationReasonCode.Running)
        self.assertEqual(out.final_reason_code, ef_py.TerminationReasonCode.Timeout)
        self.assertAlmostEqual(float(out.compiled_reward_total), 0.02, places=6)

    def test_approach_terms_are_retained_when_safety_failfast_terminates(self) -> None:
        inputs = ef_py.ExecutionStepRuntimeInputs()
        inputs.safety.finite_state_valid = True
        inputs.safety.health = 100.0
        inputs.safety.survival_reward = 0.02
        inputs.safety.airborne = True
        inputs.safety.aoa_valid = True
        inputs.safety.aoa_abs_deg = 55.0
        inputs.safety.failfast_penalty = -50.0
        inputs.has_approach = True
        inputs.approach.valid = True
        inputs.approach.ils_valid = True
        inputs.approach.ils_loc_dev = 0.0
        inputs.approach.ils_gs_dev = 0.0
        inputs.approach.capture_bonus = 5.0
        inputs.approach.capture_localizer_band = 0.2
        inputs.approach.capture_glideslope_band = 0.2

        out = ef_py.compute_execution_step_runtime(inputs)
        self.assertTrue(bool(out.valid))
        self.assertTrue(bool(out.terminated))
        self.assertTrue(bool(out.approach_evaluated))
        self.assertEqual(out.reason_code, ef_py.TerminationReasonCode.FailfastDeepStall)
        self.assertAlmostEqual(float(out.approach.approach_capture_bonus), 5.0, places=6)
        self.assertAlmostEqual(float(out.compiled_reward_total), -84.98, places=6)


class ExecutionEpisodeRuntimeTests(unittest.TestCase):
    def test_episode_runtime_aggregates_shaping_and_populates_waypoint_status(self) -> None:
        inputs = ef_py.ExecutionEpisodeRuntimeInputs()
        inputs.has_execution_step = True
        inputs.execution_step.safety.finite_state_valid = True
        inputs.execution_step.safety.health = 100.0
        inputs.execution_step.safety.survival_reward = 0.02
        inputs.execution_step.has_waypoint = True
        inputs.execution_step.waypoint.valid = True
        inputs.execution_step.waypoint.waypoint_index = 1
        inputs.execution_step.waypoint.waypoint_count = 3
        inputs.execution_step.waypoint.dist_m = 123.0
        inputs.has_flight_shaping = True
        inputs.flight_shaping.truth_speed_mps = 100.0
        inputs.flight_shaping.speed_reward_weight = 0.5

        out = ef_py.compute_execution_episode_runtime(inputs)
        self.assertTrue(bool(out.valid))
        self.assertTrue(bool(out.execution_step_evaluated))
        self.assertTrue(bool(out.flight_shaping_evaluated))
        self.assertTrue(bool(out.outcome_evaluated))
        self.assertAlmostEqual(float(out.compiled_reward_total), 50.02, places=6)
        self.assertAlmostEqual(float(out.status0), 123.0, places=6)
        self.assertAlmostEqual(float(out.status1), 1.0, places=6)
        self.assertAlmostEqual(float(out.status2), 3.0, places=6)
        self.assertAlmostEqual(float(out.status3), 0.0, places=6)
        self.assertFalse(bool(out.terminated))
        self.assertEqual(out.final_reason_code, ef_py.TerminationReasonCode.Running)


class ObjectiveRuntimeTests(unittest.TestCase):
    def test_conditional_objective_supports_dynamic_targets_and_success_shaping(self) -> None:
        spec = ef_py.ConditionalObjectiveSpec()
        spec.reward_bonus = 2200.0

        cond_alt = ef_py.ConditionalObjectiveCondition()
        cond_alt.property_code = ef_py.ConditionalObjectiveProperty.AltitudeAGL
        cond_alt.op_code = ef_py.ConditionalObjectiveOp.LessEqual
        cond_alt.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
        cond_alt.target_value = 2.5

        cond_ground = ef_py.ConditionalObjectiveCondition()
        cond_ground.property_code = ef_py.ConditionalObjectiveProperty.OnGround
        cond_ground.op_code = ef_py.ConditionalObjectiveOp.GreaterEqual
        cond_ground.target_kind = ef_py.ConditionalObjectiveTargetKind.Literal
        cond_ground.target_value = 0.5

        cond_speed = ef_py.ConditionalObjectiveCondition()
        cond_speed.property_code = ef_py.ConditionalObjectiveProperty.Speed
        cond_speed.op_code = ef_py.ConditionalObjectiveOp.LessEqual
        cond_speed.target_kind = ef_py.ConditionalObjectiveTargetKind.CommandSpeed
        cond_speed.target_scale = 1.1

        spec.conditions = [cond_alt, cond_ground, cond_speed]

        inputs = ef_py.ConditionalObjectiveInputs()
        inputs.altitude_agl_m = 1.5
        inputs.on_ground = True
        inputs.speed_mps = 95.0
        inputs.target_speed_mps = 100.0
        inputs.has_runway_cross_m = True
        inputs.runway_cross_m = 6.0
        inputs.ground_track_error_deg = 12.0

        shaping = ef_py.ObjectiveShapingConfig()
        shaping.runway_cross_penalty_weight = -0.5
        shaping.runway_cross_deadband_m = 2.0
        shaping.runway_cross_norm_m = 10.0
        shaping.runway_cross_power = 2.0
        shaping.ground_track_penalty_weight = -1.0
        shaping.ground_track_deadband_deg = 5.0
        shaping.ground_track_norm_deg = 10.0
        shaping.ground_track_power = 2.0

        products = ef_py.evaluate_conditional_objective(spec, inputs, shaping)
        self.assertTrue(bool(products.valid))
        self.assertTrue(bool(products.matched))
        self.assertAlmostEqual(float(products.status0), 1.5, places=6)
        self.assertAlmostEqual(float(products.status1), 1.0, places=6)
        self.assertAlmostEqual(float(products.status2), 95.0, places=6)
        self.assertEqual(int(products.status_count), 3)
        self.assertAlmostEqual(float(products.success_runway_cross_penalty), -0.08, places=6)
        self.assertAlmostEqual(float(products.success_ground_track_error_penalty), -0.49, places=6)
        self.assertAlmostEqual(float(products.objective_bonus), 2200.0, places=6)

    def test_conditional_objective_fails_closed_on_unknown_property(self) -> None:
        spec = ef_py.ConditionalObjectiveSpec()
        cond = ef_py.ConditionalObjectiveCondition()
        cond.property_code = ef_py.ConditionalObjectiveProperty.Unknown
        cond.op_code = ef_py.ConditionalObjectiveOp.GreaterEqual
        cond.target_value = 0.0
        spec.conditions = [cond]

        inputs = ef_py.ConditionalObjectiveInputs()
        shaping = ef_py.ObjectiveShapingConfig()
        products = ef_py.evaluate_conditional_objective(spec, inputs, shaping)
        self.assertTrue(bool(products.valid))
        self.assertFalse(bool(products.matched))
        self.assertTrue(bool(products.unknown_property))
        self.assertEqual(int(products.status_count), 0)


class TerminationRuntimeTests(unittest.TestCase):
    def test_nan_guard_returns_early_failure(self) -> None:
        inputs = ef_py.SafetyRuntimeInputs()
        inputs.finite_state_valid = False
        inputs.crash_penalty = -321.0

        out = ef_py.compute_safety_runtime(inputs)
        self.assertTrue(bool(out.valid))
        self.assertTrue(bool(out.early_return))
        self.assertTrue(bool(out.terminated))
        self.assertEqual(out.reason_code, ef_py.TerminationReasonCode.NanGuard)
        self.assertAlmostEqual(float(out.status_flag), -1.0, places=6)
        self.assertAlmostEqual(float(out.crash_penalty), -321.0, places=6)
        self.assertAlmostEqual(float(out.nan_guard_marker), 1.0, places=6)

    def test_gear_collapse_overrides_failfast_reason_but_keeps_penalty_terms(self) -> None:
        inputs = ef_py.SafetyRuntimeInputs()
        inputs.finite_state_valid = True
        inputs.health = 100.0
        inputs.survival_reward = 0.02
        inputs.airborne = True
        inputs.aoa_valid = True
        inputs.aoa_abs_deg = 60.0
        inputs.failfast_penalty = -50.0
        inputs.gear_collapsed = True
        inputs.gear_collapse_penalty = -500.0

        out = ef_py.compute_safety_runtime(inputs)
        self.assertTrue(bool(out.valid))
        self.assertTrue(bool(out.terminated))
        self.assertEqual(out.reason_code, ef_py.TerminationReasonCode.GearCollapse)
        self.assertAlmostEqual(float(out.failfast_penalty), -50.0, places=6)
        self.assertAlmostEqual(float(out.gear_collapse_penalty), -500.0, places=6)
        self.assertAlmostEqual(float(out.survival), 0.02, places=6)

    def test_off_runway_termination_respects_grace_window(self) -> None:
        inputs = ef_py.SafetyRuntimeInputs()
        inputs.finite_state_valid = True
        inputs.health = 100.0
        inputs.runway_surface_phase = True
        inputs.on_runway_task = False
        inputs.gear_stress = 0.5
        inputs.gear_stress_penalty_weight = -10.0
        inputs.off_runway_penalty = -1.0
        inputs.speed_mps = 50.0
        inputs.off_runway_steps = 3
        inputs.off_runway_terminate_speed = 40.0
        inputs.off_runway_terminate_grace_s = 0.10
        inputs.time_step_s = 0.05
        inputs.off_runway_terminate_penalty = -200.0

        out = ef_py.compute_safety_runtime(inputs)
        self.assertTrue(bool(out.terminated))
        self.assertEqual(out.reason_code, ef_py.TerminationReasonCode.OffRunwayTerminate)
        self.assertAlmostEqual(float(out.off_runway_penalty), -1.0, places=6)
        self.assertAlmostEqual(float(out.gear_stress_penalty), -5.0, places=6)
        self.assertAlmostEqual(float(out.off_runway_terminate_penalty), -200.0, places=6)

    def test_finalize_reason_maps_running_to_timeout_and_success(self) -> None:
        success = ef_py.finalize_termination_reason(
            ef_py.TerminationReasonCode.Running,
            True,
            False,
            1.0,
        )
        timeout = ef_py.finalize_termination_reason(
            ef_py.TerminationReasonCode.Running,
            False,
            True,
            0.0,
        )
        self.assertEqual(ef_py.termination_reason_name(success), "success")
        self.assertEqual(ef_py.termination_reason_name(timeout), "timeout")


if __name__ == "__main__":
    unittest.main()
