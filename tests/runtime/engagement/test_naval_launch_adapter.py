from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


class NavalLaunchAdapterTests(unittest.TestCase):
    def _entity_ref(self, entity_id: int, world_index: int = 0) -> ef_py.EngagementEntityRef:
        ref = ef_py.EngagementEntityRef()
        ref.world_index = world_index
        ref.entity_id = entity_id
        return ref

    def _tracked_surface_engagement(self) -> tuple[ef_py.SimulationKernel, int, int]:
        kernel = ef_py.SimulationKernel()
        kernel.reset(640)
        self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))

        ddg = int(
            kernel.spawn_unit(
                ef_py.Side.Blue,
                "DDG-51_Flight_I_USS_Arleigh_Burke",
                0.0,
                0.0,
                0.0,
                heading=0.0,
                pitch=0.0,
                roll=0.0,
                vx=0.0,
                vy=0.0,
                vz=0.0,
            )
        )
        target = int(
            kernel.spawn_unit(
                ef_py.Side.Red,
                "Red_Surface_Combatant_Minimal",
                0.0,
                8000.0,
                0.0,
                heading=180.0,
                pitch=0.0,
                roll=0.0,
                vx=0.0,
                vy=0.0,
                vz=0.0,
            )
        )

        detection = ef_py.Detection()
        detection.target_id = target
        detection.range = 8000.0
        detection.bearing = 0.0
        detection.elevation = 0.0
        detection.closing_speed = 0.0
        detection.signal_strength = 1.0
        detection.sensor_type = int(ef_py.SensorType.Radar)
        detection.local_sensor_hit = True
        detection.timestamp = 0.0
        kernel.set_contact_list(ddg, [detection])
        return kernel, ddg, target

    def test_legacy_naval_gun_launch_maps_to_engagement_request_and_event_shape(self) -> None:
        kernel, ddg, target = self._tracked_surface_engagement()

        request = ef_py.LaunchRequest()
        request.request_id = 64001
        request.shooter = self._entity_ref(ddg)
        request.target_entity = self._entity_ref(target)
        request.has_target_entity = True
        request.target_track_id = target
        request.has_target_track = True
        request.station_id = "naval"
        request.mount_id = "mk45_gun"
        request.requested_munition_family = "gun_5in"
        request.authority = "legacy_direct_fire"
        request.requested_time_s = 0.0
        request.merge_policy = "reject_on_conflict"

        before = kernel.debug_get_naval_weapon_counts(ddg)
        fired = bool(kernel.fire_naval_weapon(ddg, target, 2))
        after = kernel.debug_get_naval_weapon_counts(ddg)

        event = ef_py.LaunchEvent()
        event.event_id = 64002
        event.request_id = request.request_id
        event.accepted = fired
        event.rejection_reason = ""
        event.selected_launcher = request.mount_id
        event.selected_munition = request.requested_munition_family
        event.ammo_delta = int(after[2]) - int(before[2])
        event.cooldown_delta_s = 3.5
        event.spawned_munition = self._entity_ref(0)
        event.has_spawned_munition = False
        event.event_time_s = request.requested_time_s

        self.assertTrue(fired)
        self.assertEqual(request.shooter.entity_id, ddg)
        self.assertEqual(request.target_entity.entity_id, target)
        self.assertTrue(bool(request.has_target_entity))
        self.assertTrue(bool(request.has_target_track))
        self.assertEqual(request.target_track_id, target)
        self.assertEqual(request.mount_id, "mk45_gun")
        self.assertEqual(request.requested_munition_family, "gun_5in")

        self.assertEqual(int(before[1]), int(after[1]))
        self.assertEqual(int(before[2]) - 1, int(after[2]))
        self.assertEqual(int(before[3]), int(after[3]))
        self.assertEqual(event.request_id, request.request_id)
        self.assertTrue(bool(event.accepted))
        self.assertEqual(event.rejection_reason, "")
        self.assertEqual(event.selected_launcher, "mk45_gun")
        self.assertEqual(event.selected_munition, "gun_5in")
        self.assertEqual(event.ammo_delta, -1)
        self.assertAlmostEqual(event.cooldown_delta_s, 3.5, places=6)
        self.assertFalse(bool(event.has_spawned_munition))
        self.assertEqual(event.spawned_munition.entity_id, 0)


if __name__ == "__main__":
    unittest.main()
