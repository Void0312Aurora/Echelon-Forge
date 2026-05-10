from __future__ import annotations

import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

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
