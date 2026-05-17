from __future__ import annotations

import json
import tempfile
import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


class NavalSensorRealismRuntimeTests(unittest.TestCase):
    _OPEN_WATER_X = 1_000_000.0
    _OPEN_WATER_Y = 1_000_000.0

    def _kernel_with_overrides(self, overrides: dict[str, dict]) -> ef_py.SimulationKernel:
        kernel = ef_py.SimulationKernel()
        kernel.reset(7300 + len(overrides))
        self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
            json.dump({"units": list(overrides.values())}, handle)
            override_path = handle.name
        self.assertTrue(kernel.load_unit_definitions(override_path))
        return kernel

    @staticmethod
    def _find_detection(kernel: ef_py.SimulationKernel, owner_id: int, target_id: int):
        for det in kernel.get_detections(owner_id):
            if int(det.target_id) == int(target_id):
                return det
        return None

    def test_surface_radar_horizon_blocks_high_distance_surface_contact(self) -> None:
        with open(
            resolve_repo_path("examples", "config", "database", "ships", "units", "ddg51_flight_i_uss_arleigh_burke.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            ddg_def = json.load(handle)

        ddg_def["name"] = "DDG-51_Horizon_Test"
        ddg_def["mounted_sensors"] = [
            {
                "label": "horizon_test_surface_radar",
                "sensor": {
                    "type": "Radar",
                    "max_range": 46300.0,
                    "fov_deg": 360.0,
                    "scan_period": 0.5,
                    "detection_prob": 1.0,
                    "bearing_noise_std": 0.0,
                    "range_noise_std": 0.0,
                    "track_memory_s": 5.0,
                    "range_power": 1.0,
                    "aspect_influence": 0.0,
                    "reference_snr_db": 30.0,
                    "reference_range_m": 46300.0,
                    "reference_rcs_m2": 25.0,
                    "doppler_notch_width": 0.0,
                    "antenna_height_m": 25.0,
                    "target_height_bias_m": 5.0,
                    "environment_domain": "SurfaceMaritime",
                    "enforce_radar_horizon": True,
                    "enable_ducting": False,
                    "sea_clutter_enabled": False
                }
            }
        ]
        ddg_def["sensor_ref"] = ""
        ddg_def["sensor_refs"] = []

        kernel = self._kernel_with_overrides({ddg_def["name"]: ddg_def})
        kernel.set_time_step(0.5)

        ddg = kernel.spawn_unit(
            ef_py.Side.Blue,
            "DDG-51_Horizon_Test",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y,
            0.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=10.29,
            vz=0.0,
        )
        far_ship = kernel.spawn_unit(
            ef_py.Side.Red,
            "T-AKE-1_USNS_Lewis_and_Clark",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y + 70_000.0,
            0.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=0.0,
            vz=0.0,
        )
        self.assertGreater(int(far_ship), 0)

        saw_surface_track = False
        for _ in range(20):
            kernel.step()
            obs = kernel.get_agent_observation(int(ddg))
            saw_surface_track = saw_surface_track or any(int(track.id) == int(far_ship) for track in obs.contacts)

        self.assertFalse(saw_surface_track)

    def test_ducting_override_extends_surface_radar_range(self) -> None:
        with open(
            resolve_repo_path("examples", "config", "database", "ships", "units", "ddg51_flight_i_uss_arleigh_burke.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            ddg_def = json.load(handle)

        ddg_def["name"] = "DDG-51_Ducting_Test"
        ddg_def["mounted_sensors"] = [
            {
                "label": "ducting_test_surface_radar",
                "sensor": {
                    "type": "Radar",
                    "max_range": 46300.0,
                    "fov_deg": 360.0,
                    "scan_period": 0.5,
                    "detection_prob": 1.0,
                    "bearing_noise_std": 0.0,
                    "range_noise_std": 0.0,
                    "track_memory_s": 5.0,
                    "range_power": 1.0,
                    "aspect_influence": 0.0,
                    "reference_snr_db": 30.0,
                    "reference_range_m": 46300.0,
                    "reference_rcs_m2": 25.0,
                    "antenna_height_m": 25.0,
                    "target_height_bias_m": 5.0,
                    "environment_domain": "SurfaceMaritime",
                    "enforce_radar_horizon": True,
                    "enable_ducting": True,
                    "ducting_gain_factor": 1.35,
                    "ducting_max_bonus_m": 18000.0,
                    "sea_clutter_enabled": False
                }
            }
        ]
        ddg_def["sensor_ref"] = ""
        ddg_def["sensor_refs"] = []

        kernel = self._kernel_with_overrides({ddg_def["name"]: ddg_def})
        kernel.set_time_step(0.5)
        ddg = kernel.spawn_unit(
            ef_py.Side.Blue,
            "DDG-51_Ducting_Test",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y,
            0.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=10.29,
            vz=0.0,
        )
        target_ship = kernel.spawn_unit(
            ef_py.Side.Red,
            "T-AKE-1_USNS_Lewis_and_Clark",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y + 50_000.0,
            0.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-25.0,
            vz=0.0,
        )

        saw_target = False
        for _ in range(40):
            kernel.step()
            obs = kernel.get_agent_observation(int(ddg))
            saw_target = saw_target or any(int(track.id) == int(target_ship) for track in obs.contacts)

        self.assertTrue(saw_target)

    def test_surface_radar_sea_state_penalty_can_suppress_detection(self) -> None:
        with open(
            resolve_repo_path("examples", "config", "database", "ships", "units", "ddg51_flight_i_uss_arleigh_burke.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            ddg_def = json.load(handle)

        ddg_def["name"] = "DDG-51_SeaState_Test"
        ddg_def["ship_platform"]["sea_state"] = 6.0
        ddg_def["mounted_sensors"] = [
            {
                "label": "sea_state_penalty_radar",
                "sensor": {
                    "type": "Radar",
                    "max_range": 46300.0,
                    "fov_deg": 360.0,
                    "scan_period": 1.0,
                    "detection_prob": 1.0,
                    "bearing_noise_std": 0.0,
                    "range_noise_std": 0.0,
                    "track_memory_s": 5.0,
                    "range_power": 1.0,
                    "aspect_influence": 0.0,
                    "antenna_height_m": 25.0,
                    "target_height_bias_m": 5.0,
                    "environment_domain": "SurfaceMaritime",
                    "enforce_radar_horizon": True,
                    "sea_clutter_enabled": True,
                    "sea_clutter_sensitivity": 1.0,
                    "sea_state_loss_per_level": 0.16,
                    "enable_ducting": False
                }
            }
        ]
        ddg_def["sensor_ref"] = ""
        ddg_def["sensor_refs"] = []

        kernel = self._kernel_with_overrides({ddg_def["name"]: ddg_def})
        ddg = kernel.spawn_unit(
            ef_py.Side.Blue,
            "DDG-51_SeaState_Test",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y,
            0.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=10.29,
            vz=0.0,
        )
        target_ship = kernel.spawn_unit(
            ef_py.Side.Red,
            "T-AKE-1_USNS_Lewis_and_Clark",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y + 42_000.0,
            0.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=0.0,
            vz=0.0,
        )

        saw_target = False
        for _ in range(20):
            kernel.step()
            obs = kernel.get_agent_observation(int(ddg))
            saw_target = saw_target or any(int(track.id) == int(target_ship) for track in obs.contacts)

        self.assertFalse(saw_target)

    def test_environment_maritime_state_override_drives_surface_radar_penalty(self) -> None:
        with open(
            resolve_repo_path("examples", "config", "database", "ships", "units", "ddg51_flight_i_uss_arleigh_burke.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            ddg_def = json.load(handle)

        ddg_def["name"] = "DDG-51_Global_Maritime_Radar_Test"
        ddg_def["ship_platform"]["sea_state"] = 0.0
        ddg_def["mounted_sensors"] = [
            {
                "label": "global_maritime_penalty_radar",
                "sensor": {
                    "type": "Radar",
                    "max_range": 46300.0,
                    "fov_deg": 360.0,
                    "scan_period": 1.0,
                    "detection_prob": 1.0,
                    "bearing_noise_std": 0.0,
                    "range_noise_std": 0.0,
                    "track_memory_s": 5.0,
                    "range_power": 1.0,
                    "aspect_influence": 0.0,
                    "reference_snr_db": 32.0,
                    "reference_range_m": 30000.0,
                    "reference_rcs_m2": 25.0,
                    "antenna_height_m": 25.0,
                    "target_height_bias_m": 5.0,
                    "environment_domain": "SurfaceMaritime",
                    "enforce_radar_horizon": True,
                    "sea_clutter_enabled": True,
                    "sea_clutter_sensitivity": 1.0,
                    "sea_state_loss_per_level": 0.16,
                    "enable_ducting": False,
                    "doppler_notch_width": 0.001,
                },
            }
        ]
        ddg_def["sensor_ref"] = ""
        ddg_def["sensor_refs"] = []

        target_offset_m = 12_000.0

        calm_kernel = self._kernel_with_overrides({ddg_def["name"]: ddg_def})
        calm_kernel.set_time_step(0.5)
        calm_ddg = calm_kernel.spawn_unit(
            ef_py.Side.Blue,
            "DDG-51_Global_Maritime_Radar_Test",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y,
            0.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=10.29,
            vz=0.0,
        )
        calm_target = calm_kernel.spawn_unit(
            ef_py.Side.Red,
            "T-AKE-1_USNS_Lewis_and_Clark",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y + target_offset_m,
            0.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=0.0,
            vz=0.0,
        )

        calm_detection = None
        for _ in range(10):
            calm_kernel.step()
            calm_detection = self._find_detection(calm_kernel, int(calm_ddg), int(calm_target))
            if calm_detection is not None:
                break

        rough_kernel = self._kernel_with_overrides({ddg_def["name"]: ddg_def})
        rough_kernel.set_time_step(0.5)
        rough_kernel.set_maritime_state(6.0, 90.0, 8.0)
        rough_ddg = rough_kernel.spawn_unit(
            ef_py.Side.Blue,
            "DDG-51_Global_Maritime_Radar_Test",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y,
            0.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=10.29,
            vz=0.0,
        )
        rough_target = rough_kernel.spawn_unit(
            ef_py.Side.Red,
            "T-AKE-1_USNS_Lewis_and_Clark",
            self._OPEN_WATER_X,
            self._OPEN_WATER_Y + target_offset_m,
            0.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=0.0,
            vz=0.0,
        )

        rough_detection = None
        for _ in range(10):
            rough_kernel.step()
            rough_detection = self._find_detection(rough_kernel, int(rough_ddg), int(rough_target))
            if rough_detection is not None:
                break

        self.assertIsNotNone(calm_detection)
        self.assertIsNotNone(rough_detection)
        self.assertGreater(float(calm_detection.snr_db), float(rough_detection.snr_db) + 2.0)

    def test_surface_los_accepts_near_origin_sea_level_contacts_when_maritime_state_is_active(self) -> None:
        with open(
            resolve_repo_path("examples", "config", "database", "ships", "units", "ddg51_flight_i_uss_arleigh_burke.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            ddg_def = json.load(handle)

        ddg_def["name"] = "DDG-51_Surface_LOS_Test"
        ddg_def["mounted_sensors"] = [
            {
                "label": "surface_los_test_radar",
                "sensor": {
                    "type": "Radar",
                    "max_range": 30000.0,
                    "fov_deg": 360.0,
                    "scan_period": 0.5,
                    "detection_prob": 1.0,
                    "bearing_noise_std": 0.0,
                    "range_noise_std": 0.0,
                    "track_memory_s": 5.0,
                    "range_power": 1.0,
                    "aspect_influence": 0.0,
                    "reference_snr_db": 32.0,
                    "reference_range_m": 30000.0,
                    "reference_rcs_m2": 25.0,
                    "antenna_height_m": 25.0,
                    "target_height_bias_m": 5.0,
                    "environment_domain": "SurfaceMaritime",
                    "enforce_radar_horizon": True,
                    "sea_clutter_enabled": False,
                    "enable_ducting": False,
                    "doppler_notch_width": 0.001,
                },
            }
        ]
        ddg_def["sensor_ref"] = ""
        ddg_def["sensor_refs"] = []

        kernel = self._kernel_with_overrides({ddg_def["name"]: ddg_def})
        kernel.set_time_step(0.5)
        kernel.set_maritime_state(3.0, 45.0, 7.5)
        kernel.set_terrain_type("flat")
        ddg = kernel.spawn_unit(
            ef_py.Side.Blue,
            "DDG-51_Surface_LOS_Test",
            0.0,
            0.0,
            0.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=8.0,
            vz=0.0,
        )
        target = kernel.spawn_unit(
            ef_py.Side.Red,
            "Red_Surface_Combatant_Minimal",
            0.0,
            12_000.0,
            0.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=0.0,
            vz=0.0,
        )

        detection = None
        for _ in range(10):
            kernel.step()
            detection = self._find_detection(kernel, int(ddg), int(target))
            if detection is not None:
                break

        self.assertIsNotNone(detection)


if __name__ == "__main__":
    unittest.main()
