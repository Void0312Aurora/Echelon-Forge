from __future__ import annotations

import base64
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

from tools.diagnostics.generate_exact_world_step_first_scope_chain_trace import (  # noqa: E402
    generate_cpu_exact_world_step_first_scope_chain_trace,
)

try:
    import torch
except Exception:  # pragma: no cover - torch is expected in the maintained runtime env
    torch = None

import ef_py  # noqa: E402


def _entity_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
    ref = ef_py.WorldEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


class GpuRuntimeBindingTests(unittest.TestCase):
    def test_visual_runtime_probe_bindings_are_available(self) -> None:
        info = ef_py.probe_gpu_device()
        self.assertTrue(hasattr(info, "cuda_runtime_built"))
        self.assertTrue(hasattr(info, "cuda_runtime_available"))
        self.assertTrue(hasattr(info, "device_count"))
        self.assertTrue(hasattr(info, "device_name"))

        stats = ef_py.last_visual_experiment_stats()
        self.assertTrue(hasattr(stats, "used_cuda"))
        self.assertTrue(hasattr(stats, "total_ms"))

        obs_stats = ef_py.last_execution_observation_stats()
        self.assertTrue(hasattr(obs_stats, "used_cuda"))
        self.assertTrue(hasattr(obs_stats, "total_ms"))

        shaping_stats = ef_py.last_flight_shaping_stats()
        self.assertTrue(hasattr(shaping_stats, "used_cuda"))
        self.assertTrue(hasattr(shaping_stats, "total_ms"))

    def test_flight_shaping_batch_binding_matches_reference(self) -> None:
        inputs = ef_py.FlightShapingRuntimeInputs()
        inputs.truth_altitude_m = 120.0
        inputs.truth_speed_mps = 95.0
        inputs.prev_altitude_m = 100.0
        inputs.prev_ias_mps = 80.0
        inputs.curr_ias_mps = 100.0
        inputs.curr_alt_baro_m = 120.0
        inputs.curr_alt_agl_m = 4.0
        inputs.curr_gear_fraction = 0.5
        inputs.curr_roll_deg = 2.0
        inputs.curr_pitch_deg = 10.0
        inputs.curr_beta_deg = 0.0
        inputs.curr_yaw_rate_deg_s = 0.0
        inputs.curr_g_load = 1.0
        inputs.step_count = 30
        inputs.target_altitude_m = 500.0
        inputs.target_speed_mps = 150.0
        inputs.heading_error_deg = 2.0
        inputs.ground_track_error_deg = 0.0
        inputs.preliftoff = True
        inputs.on_runway_task = True
        inputs.airborne = False
        inputs.liftoff_awarded = False
        inputs.gear_bonus_awarded = False
        inputs.altitude_progress_weight = 0.05
        inputs.speed_progress_weight = 0.02
        inputs.liftoff_bonus = 5.0
        inputs.liftoff_speed_threshold_mps = 80.0
        inputs.liftoff_alt_threshold_m = 3.0
        inputs.rotation_reward_weight = 0.5
        inputs.rotation_speed_threshold_mps = 80.0
        inputs.rotation_alt_threshold_m = 5.0
        inputs.rotation_pitch_cap_deg = 15.0
        inputs.heading_error_weight = -0.1
        inputs.heading_hold_deadband_deg = 3.0
        inputs.heading_hold_bonus = 1.0
        inputs.speed_reward_weight = 0.01

        reference = ef_py.compute_flight_shaping_terms(inputs)
        compiled_batch = ef_py.compute_flight_shaping_batch([inputs], False)
        gpu_batch = ef_py.compute_flight_shaping_batch([inputs], True)

        self.assertEqual(len(compiled_batch), 1)
        self.assertEqual(len(gpu_batch), 1)
        for got in (compiled_batch[0], gpu_batch[0]):
            self.assertAlmostEqual(float(reference.altitude_progress), float(got.altitude_progress), places=6)
            self.assertAlmostEqual(float(reference.speed_progress), float(got.speed_progress), places=6)
            self.assertAlmostEqual(float(reference.liftoff_bonus), float(got.liftoff_bonus), places=6)
            self.assertEqual(bool(reference.next_liftoff_awarded), bool(got.next_liftoff_awarded))
            self.assertAlmostEqual(float(reference.rotation_reward), float(got.rotation_reward), places=6)
            self.assertAlmostEqual(float(reference.heading_error_penalty), float(got.heading_error_penalty), places=6)
            self.assertAlmostEqual(float(reference.heading_hold_bonus), float(got.heading_hold_bonus), places=6)
            self.assertAlmostEqual(float(reference.speed_reward), float(got.speed_reward), places=6)

    def test_interaction_broadphase_binding_matches_reference_superset(self) -> None:
        config = ef_py.InteractionBroadphaseConfig()
        config.cell_size_m = 5000.0
        config.max_entity_radius_m = 250.0
        config.entities_per_world = 8
        config.hash_bucket_count = 256
        config.bucket_capacity = 16

        entities = []
        for idx in range(8):
            entity = ef_py.InteractionEntityPacked()
            entity.world_index = 0
            entity.local_index = idx
            entity.x = float(idx * 1000.0)
            entity.y = 0.0
            entity.z = 1000.0
            entity.bounding_radius_m = 50.0
            entities.append(entity)

        query = ef_py.InteractionQueryPacked()
        query.world_index = 0
        query.x = 1500.0
        query.y = 0.0
        query.z = 1000.0
        query.range_m = 2500.0

        reference = np.asarray(
            ef_py.build_interaction_broadphase_batch_numpy(entities, [query], config, False)
        )
        experiment = np.asarray(
            ef_py.build_interaction_broadphase_batch_numpy(entities, [query], config, True)
        )
        self.assertEqual(reference.shape, experiment.shape)
        self.assertTrue(np.all((reference.astype(np.uint32) & ~experiment.astype(np.uint32)) == 0))

    def test_world_batch_step_binding_matches_reference(self) -> None:
        states = []
        for idx in range(16):
            state = ef_py.WorldBatchStepState()
            state.x_m = float(idx * 100.0)
            state.y_m = float(-idx * 50.0)
            state.z_m = 1000.0 + idx
            state.vx_mps = 100.0 + idx
            state.vy_mps = -20.0 + idx * 0.5
            state.vz_mps = 1.0
            state.wind_vx_mps = 5.0
            state.wind_vy_mps = -2.0
            state.cmd_vx_mps = 120.0
            state.cmd_vy_mps = 0.0
            state.cmd_vz_mps = 0.0
            state.max_delta_vxy_mps_per_step = 1.0
            state.max_delta_vz_mps_per_step = 0.5
            state.time_step_s = 0.05
            state.fuel_kg = 1500.0
            state.fuel_idle_burn_kgps = 0.2
            state.fuel_burn_per_speed_kgps_per_mps = 0.001
            states.append(state)

        reference = ef_py.step_world_batch_state_batch_reference(states, 32)
        experiment = ef_py.step_world_batch_state_batch(states, 32, False)

        self.assertEqual(len(reference), len(experiment))
        for ref, got in zip(reference, experiment):
            self.assertAlmostEqual(ref.x_m, got.x_m, places=9)
            self.assertAlmostEqual(ref.y_m, got.y_m, places=9)
            self.assertAlmostEqual(ref.z_m, got.z_m, places=9)
            self.assertAlmostEqual(ref.vx_mps, got.vx_mps, places=9)
            self.assertAlmostEqual(ref.vy_mps, got.vy_mps, places=9)
            self.assertAlmostEqual(ref.vz_mps, got.vz_mps, places=9)
            self.assertAlmostEqual(ref.fuel_kg, got.fuel_kg, places=9)
            self.assertAlmostEqual(ref.mission_time_s, got.mission_time_s, places=9)

    def test_exact_first_scope_resident_cuda_upload_replay_download_matches_trace(self) -> None:
        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.skipTest("CUDA runtime is not available")
        trace = generate_cpu_exact_world_step_first_scope_chain_trace(seed=47, time_step_s=0.05)
        initial_packed = base64.b64decode(trace["initial_exact_state_packed_b64"])
        expected_final_packed = base64.b64decode(trace["final_record"]["packed_exact_state_b64"])

        self.assertTrue(ef_py.upload_exact_world_step_first_scope_chain_cuda_states_packed(initial_packed))
        self.assertEqual(int(ef_py.last_exact_world_step_first_scope_chain_cuda_output_state_count()), 2)
        self.assertGreater(int(ef_py.last_exact_world_step_first_scope_chain_cuda_output_device_ptr()), 0)
        self.assertTrue(ef_py.replay_exact_world_step_first_scope_chain_cuda_device_sequence())
        actual_final_packed = bytes(ef_py.download_exact_world_step_first_scope_chain_cuda_states_packed())

        expected_signatures = ef_py.exact_world_step_states_v1_apply_signatures_packed(expected_final_packed)
        actual_signatures = ef_py.exact_world_step_states_v1_apply_signatures_packed(actual_final_packed)
        self.assertEqual(expected_signatures, actual_signatures)
        expected_digests = ef_py.exact_world_step_state_v1_component_digests_packed(expected_final_packed)
        actual_digests = ef_py.exact_world_step_state_v1_component_digests_packed(actual_final_packed)
        self.assertEqual(expected_digests, actual_digests)

        stats = ef_py.last_exact_world_step_first_scope_chain_cuda_stats()
        self.assertEqual(int(stats.state_count), 2)
        self.assertEqual(int(stats.missile_count), 1)
        self.assertTrue(bool(stats.used_cuda))
        self.assertGreaterEqual(float(stats.host_to_device_ms), 0.0)
        self.assertGreaterEqual(float(stats.kernel_ms), 0.0)
        self.assertGreaterEqual(float(stats.device_to_host_ms), 0.0)

    def test_exact_world_step_state_packed_roundtrip_restores_apply_signature(self) -> None:
        runtime = ef_py.WorldBatchRuntime(1)
        self.assertTrue(runtime.load_database(resolve_repo_path("examples", "config", "database")))
        runtime.reset_batch([77])
        runtime.set_time_step(0.05)

        entity_id = runtime.world(0).spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            -500.0,
            200.0,
            1200.0,
            90.0,
            0.0,
            0.0,
            190.0,
            0.0,
            0.0,
        )

        cmd = ef_py.MissionCommand()
        cmd.command_code = 3
        cmd.cmd_heading_deg = 35.0
        cmd.cmd_altitude_m = 1600.0
        cmd.cmd_speed_mps = 220.0
        cmd.active = True
        runtime.world(0).set_mission_command(int(entity_id), cmd)

        ref = ef_py.WorldEntityRef()
        ref.world_index = 0
        ref.entity_id = int(entity_id)
        refs = [ref]

        packed_before = runtime.extract_exact_world_step_states_v1_batch_packed(refs)
        self.assertEqual(len(packed_before), int(ef_py.exact_world_step_state_v1_size_bytes()))
        sig_before = ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_before)
        self.assertEqual(len(sig_before), 1)

        runtime.step_batch()
        runtime.step_batch()
        packed_after = runtime.extract_exact_world_step_states_v1_batch_packed(refs)
        sig_after = ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_after)
        self.assertNotEqual(sig_before, sig_after)

        runtime.set_time_step(0.2)
        runtime.apply_exact_world_step_states_v1_batch_packed(refs, packed_before)
        self.assertAlmostEqual(float(runtime.world(0).get_time_step()), 0.05, places=9)

        packed_restored = runtime.extract_exact_world_step_states_v1_batch_packed(refs)
        sig_restored = ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_restored)
        self.assertEqual(sig_before, sig_restored)

    def test_exact_world_step_hidden_surfaces_packed_match_live_runtime(self) -> None:
        runtime = ef_py.WorldBatchRuntime(1)
        self.assertTrue(runtime.load_database(resolve_repo_path("examples", "config", "database")))
        runtime.reset_batch([83])
        runtime.set_time_step(0.05)

        entity_id = runtime.world(0).spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            -650.0,
            80.0,
            1150.0,
            55.0,
            0.0,
            0.0,
            135.0,
            155.0,
            0.0,
        )
        runtime.world(0).set_command(int(entity_id), 90.0, 235.0, 1450.0)
        runtime.step_batch()

        refs = [_entity_ref(0, int(entity_id))]
        packed = runtime.extract_exact_world_step_states_v1_batch_packed(refs)
        packed_hidden = ef_py.exact_world_step_state_v1_hidden_surfaces_packed(packed)
        live_hidden = runtime.extract_exact_world_step_state_v1_hidden_surfaces_batch(refs)

        self.assertEqual(packed_hidden, live_hidden)
        self.assertEqual(len(live_hidden), 1)
        self.assertIn("environment_sample", live_hidden[0])
        self.assertIn("angular_velocity", live_hidden[0])
        self.assertIn("force_accumulator", live_hidden[0])
        self.assertIn("aero_state", live_hidden[0])
        self.assertIn("control_law_state", live_hidden[0])
        self.assertIn("egi", live_hidden[0])

    def test_exact_world_step_prototype_packed_matches_reference_and_can_write_back(self) -> None:
        runtime = ef_py.WorldBatchRuntime(2)
        self.assertTrue(runtime.load_database(resolve_repo_path("examples", "config", "database")))
        runtime.reset_batch([23, 31])
        runtime.set_time_step(0.05)

        eid0 = runtime.world(0).spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            -700.0,
            50.0,
            1000.0,
            35.0,
            0.0,
            0.0,
            120.0,
            160.0,
            0.0,
        )
        eid1 = runtime.world(1).spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            -1100.0,
            320.0,
            1180.0,
            70.0,
            0.0,
            0.0,
            95.0,
            175.0,
            0.0,
        )

        runtime.world(0).set_command(int(eid0), 90.0, 240.0, 1500.0)
        runtime.world(1).set_command(int(eid1), 15.0, 210.0, 950.0)
        runtime.world(0).set_command_lag(int(eid0), 0.35, 0.8, 1.2)
        runtime.world(1).set_command_lag(int(eid1), 0.5, 1.0, 1.5)

        refs = [_entity_ref(0, int(eid0)), _entity_ref(1, int(eid1))]
        packed_initial = runtime.extract_exact_world_step_states_v1_batch_packed(refs)

        packed_reference = ef_py.step_exact_world_step_states_v1_prototype_packed(packed_initial, 12, False)
        packed_candidate = ef_py.step_exact_world_step_states_v1_prototype_packed(packed_initial, 12, True)

        runtime.apply_exact_world_step_states_v1_batch_packed(refs, packed_reference)
        truth_reference = runtime.get_agent_observations_batch(refs)
        inst_reference = runtime.get_instrument_states_batch(refs)

        runtime.apply_exact_world_step_states_v1_batch_packed(refs, packed_candidate)
        truth_candidate = runtime.get_agent_observations_batch(refs)
        inst_candidate = runtime.get_instrument_states_batch(refs)

        for truth_ref, truth_gpu in zip(truth_reference, truth_candidate):
            self.assertAlmostEqual(float(truth_ref.x), float(truth_gpu.x), places=6)
            self.assertAlmostEqual(float(truth_ref.y), float(truth_gpu.y), places=6)
            self.assertAlmostEqual(float(truth_ref.z), float(truth_gpu.z), places=6)
            self.assertAlmostEqual(float(truth_ref.vx), float(truth_gpu.vx), places=6)
            self.assertAlmostEqual(float(truth_ref.vy), float(truth_gpu.vy), places=6)
            self.assertAlmostEqual(float(truth_ref.vz), float(truth_gpu.vz), places=6)
            self.assertAlmostEqual(float(truth_ref.heading), float(truth_gpu.heading), places=6)
            self.assertAlmostEqual(float(truth_ref.speed), float(truth_gpu.speed), places=6)

        for inst_ref, inst_gpu in zip(inst_reference, inst_candidate):
            self.assertAlmostEqual(float(inst_ref.alt_baro), float(inst_gpu.alt_baro), places=6)
            self.assertAlmostEqual(float(inst_ref.alt_radar), float(inst_gpu.alt_radar), places=6)
            self.assertAlmostEqual(float(inst_ref.ias), float(inst_gpu.ias), places=6)
            self.assertAlmostEqual(float(inst_ref.heading), float(inst_gpu.heading), places=6)
            self.assertAlmostEqual(float(inst_ref.pitch), float(inst_gpu.pitch), places=6)
            self.assertAlmostEqual(float(inst_ref.roll), float(inst_gpu.roll), places=6)
            self.assertAlmostEqual(float(inst_ref.fuel_internal), float(inst_gpu.fuel_internal), places=6)
            self.assertAlmostEqual(float(inst_ref.fuel_external), float(inst_gpu.fuel_external), places=6)
            self.assertAlmostEqual(float(inst_ref.cmd_heading), float(inst_gpu.cmd_heading), places=6)
            self.assertAlmostEqual(float(inst_ref.cmd_alt), float(inst_gpu.cmd_alt), places=6)
            self.assertAlmostEqual(float(inst_ref.cmd_speed), float(inst_gpu.cmd_speed), places=6)

        sig_candidate = ef_py.exact_world_step_states_v1_apply_signatures_packed(packed_candidate)
        sig_live = runtime.extract_exact_world_step_state_v1_apply_signatures_batch(refs)
        self.assertEqual(sig_candidate, sig_live)

        stats = ef_py.last_exact_world_step_prototype_stats()
        self.assertTrue(hasattr(stats, "used_cuda"))
        self.assertTrue(hasattr(stats, "total_ms"))
        if ef_py.probe_gpu_device().cuda_runtime_available:
            self.assertTrue(bool(stats.used_cuda))

    def test_execution_observation_export_dlpack_matches_host(self) -> None:
        if torch is None:
            self.skipTest("torch is not available")
        if not hasattr(ef_py, "compute_execution_observation_batch_export"):
            self.skipTest("execution observation export binding is not available")

        sim = ef_py.SimulationKernel()
        self.assertTrue(sim.load_database(resolve_repo_path("examples", "config", "database")))
        entity_id = sim.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            0.0,
            0.0,
            1200.0,
            90.0,
            0.0,
            0.0,
            190.0,
            0.0,
            0.0,
        )
        inst = sim.get_instrument_state(int(entity_id))
        truth = sim.get_agent_observation(int(entity_id))

        mission_inputs = ef_py.MissionObservationInputs()
        mission_inputs.mode_code = 2
        mission_inputs.command_code = 3.0
        mission_inputs.target_heading_deg = 90.0
        mission_inputs.target_altitude_m = 1200.0
        mission_inputs.target_speed_mps = 190.0

        ils_batch = np.zeros((2, 4), dtype=np.float32)
        inst_out, contacts_out, rwr_out, mission_out, device_view = ef_py.compute_execution_observation_batch_export(
            [inst, inst],
            [truth, truth],
            [mission_inputs, mission_inputs],
            ils_batch,
            10,
            4,
            True,
        )

        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.assertIsNone(device_view)
            return

        self.assertIsNotNone(device_view)
        tensor = torch.from_dlpack(device_view)
        host_flat = np.concatenate(
            [
                np.asarray(inst_out, dtype=np.float32).reshape(2, -1),
                np.asarray(contacts_out, dtype=np.float32).reshape(2, -1),
                np.asarray(rwr_out, dtype=np.float32).reshape(2, -1),
                np.asarray(mission_out, dtype=np.float32).reshape(2, -1),
            ],
            axis=1,
        )
        self.assertEqual(tuple(tensor.shape), tuple(host_flat.shape))
        self.assertTrue(np.allclose(tensor.detach().cpu().numpy(), host_flat, atol=1.0e-6))

    def test_world_batch_visual_export_dlpack_matches_host(self) -> None:
        if torch is None:
            self.skipTest("torch is not available")
        if not hasattr(ef_py, "compute_world_batch_visual_observation_batch_export"):
            self.skipTest("world batch visual export binding is not available")

        runtime = ef_py.WorldBatchRuntime(2)
        self.assertTrue(runtime.load_database(resolve_repo_path("examples", "config", "database")))

        refs = []
        for world_index in range(2):
            world = runtime.world(world_index)
            world.set_terrain_type("flat")
            entity_id = world.spawn_unit(
                ef_py.Side.Blue,
                "F-16C_Block50",
                0.0,
                float(world_index * 100.0),
                1200.0,
                90.0,
                0.0,
                0.0,
                190.0,
                0.0,
                0.0,
            )
            ref = ef_py.WorldEntityRef()
            ref.world_index = int(world_index)
            ref.entity_id = int(entity_id)
            refs.append(ref)

        visual_out, device_view = ef_py.compute_world_batch_visual_observation_batch_export(
            runtime,
            refs,
            2,
            True,
        )

        info = ef_py.probe_gpu_device()
        if not bool(info.cuda_runtime_available):
            self.assertIsNone(device_view)
            return

        self.assertIsNotNone(device_view)
        tensor = torch.from_dlpack(device_view)
        host_visual = np.asarray(visual_out, dtype=np.float32)
        self.assertEqual(tuple(tensor.shape), tuple(host_visual.shape))
        self.assertTrue(np.allclose(tensor.detach().cpu().numpy(), host_visual, atol=1.0e-6))


if __name__ == "__main__":
    unittest.main()
