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

    def _naval_launch_request(
        self,
        *,
        request_id: int,
        shooter_id: int,
        target_id: int,
        target_track_id: int,
        has_target_track: bool,
        station_id: str,
        mount_id: str,
        requested_munition_family: str,
        authority: str,
        requested_time_s: float = 0.0,
    ) -> ef_py.LaunchRequest:
        request = ef_py.LaunchRequest()
        request.request_id = request_id
        request.shooter = self._entity_ref(shooter_id)
        request.target_entity = self._entity_ref(target_id)
        request.has_target_entity = True
        request.target_track_id = target_track_id
        request.has_target_track = has_target_track
        request.station_id = station_id
        request.mount_id = mount_id
        request.requested_munition_family = requested_munition_family
        request.authority = authority
        request.requested_time_s = requested_time_s
        request.merge_policy = "reject_on_conflict"
        return request

    def _naval_launch_event(
        self,
        *,
        event_id: int,
        request: ef_py.LaunchRequest,
        accepted: bool,
        selected_launcher: str,
        selected_munition: str,
        ammo_delta: int,
        cooldown_delta_s: float,
        spawned_munition_id: int = 0,
        rejection_reason: str = "",
    ) -> ef_py.LaunchEvent:
        event = ef_py.LaunchEvent()
        event.event_id = event_id
        event.request_id = request.request_id
        event.accepted = accepted
        event.rejection_reason = rejection_reason
        event.selected_launcher = selected_launcher
        event.selected_munition = selected_munition
        event.ammo_delta = ammo_delta
        event.cooldown_delta_s = cooldown_delta_s
        event.spawned_munition = self._entity_ref(spawned_munition_id)
        event.has_spawned_munition = spawned_munition_id != 0
        event.event_time_s = request.requested_time_s
        return event

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

    def _air_target_engagement(
        self,
        *,
        with_track: bool,
    ) -> tuple[ef_py.SimulationKernel, int, int]:
        kernel = ef_py.SimulationKernel()
        kernel.reset(641)
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
                vx=10.29,
                vy=0.0,
                vz=0.0,
            )
        )
        target = int(
            kernel.spawn_unit(
                ef_py.Side.Red,
                "Aircraft",
                0.0,
                15000.0,
                3000.0,
                heading=180.0,
                pitch=0.0,
                roll=0.0,
                vx=0.0,
                vy=-180.0,
                vz=0.0,
            )
        )

        if with_track:
            detection = ef_py.Detection()
            detection.target_id = target
            detection.range = 15000.0
            detection.bearing = 0.0
            detection.elevation = 11.0
            detection.closing_speed = 180.0
            detection.signal_strength = 1.0
            detection.sensor_type = int(ef_py.SensorType.Radar)
            detection.local_sensor_hit = True
            detection.timestamp = 0.0
            kernel.set_contact_list(ddg, [detection])
        return kernel, ddg, target

    def test_legacy_naval_gun_launch_maps_to_engagement_request_and_event_shape(self) -> None:
        kernel, ddg, target = self._tracked_surface_engagement()

        request = self._naval_launch_request(
            request_id=64001,
            shooter_id=ddg,
            target_id=target,
            target_track_id=target,
            has_target_track=True,
            station_id="naval",
            mount_id="mk45_gun",
            requested_munition_family="gun_5in",
            authority="legacy_direct_fire",
        )

        before = kernel.debug_get_naval_weapon_counts(ddg)
        fired = bool(kernel.fire_naval_weapon(ddg, target, 2))
        after = kernel.debug_get_naval_weapon_counts(ddg)

        event = self._naval_launch_event(
            event_id=64002,
            request=request,
            accepted=fired,
            selected_launcher=request.mount_id,
            selected_munition=request.requested_munition_family,
            ammo_delta=int(after[2]) - int(before[2]),
            cooldown_delta_s=3.5,
        )

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

    def test_legacy_naval_vls_fire_missile_maps_to_accepted_launch_request_and_event_shape(self) -> None:
        kernel, ddg, target = self._air_target_engagement(with_track=True)

        request = self._naval_launch_request(
            request_id=64101,
            shooter_id=ddg,
            target_id=target,
            target_track_id=target,
            has_target_track=True,
            station_id="naval:vls",
            mount_id="forward_vls_sam",
            requested_munition_family="vls_sam",
            authority="legacy_fire_missile",
        )

        before = kernel.debug_get_naval_weapon_counts(ddg)
        missile_id = int(kernel.fire_missile(ddg, target))
        after = kernel.debug_get_naval_weapon_counts(ddg)
        event = self._naval_launch_event(
            event_id=64102,
            request=request,
            accepted=missile_id > 0,
            selected_launcher=request.mount_id,
            selected_munition=request.requested_munition_family,
            ammo_delta=int(after[1]) - int(before[1]),
            cooldown_delta_s=2.0,
            spawned_munition_id=missile_id,
        )

        self.assertGreater(missile_id, 0)
        self.assertEqual(request.shooter.entity_id, ddg)
        self.assertEqual(request.target_entity.entity_id, target)
        self.assertTrue(bool(request.has_target_entity))
        self.assertTrue(bool(request.has_target_track))
        self.assertEqual(request.target_track_id, target)
        self.assertEqual(request.station_id, "naval:vls")
        self.assertEqual(request.mount_id, "forward_vls_sam")
        self.assertEqual(request.requested_munition_family, "vls_sam")
        self.assertEqual(request.authority, "legacy_fire_missile")

        self.assertEqual(int(before[1]) - 1, int(after[1]))
        self.assertEqual(int(before[2]), int(after[2]))
        self.assertEqual(int(before[3]), int(after[3]))
        self.assertEqual(event.request_id, request.request_id)
        self.assertTrue(bool(event.accepted))
        self.assertEqual(event.rejection_reason, "")
        self.assertEqual(event.selected_launcher, request.mount_id)
        self.assertEqual(event.selected_munition, request.requested_munition_family)
        self.assertEqual(event.ammo_delta, -1)
        self.assertAlmostEqual(event.cooldown_delta_s, 2.0, places=6)
        self.assertTrue(bool(event.has_spawned_munition))
        self.assertEqual(event.spawned_munition.entity_id, missile_id)

    def test_legacy_naval_vls_fire_missile_without_track_maps_to_rejected_launch_event_shape(self) -> None:
        kernel, ddg, target = self._air_target_engagement(with_track=False)

        request = self._naval_launch_request(
            request_id=64103,
            shooter_id=ddg,
            target_id=target,
            target_track_id=0,
            has_target_track=False,
            station_id="naval:vls",
            mount_id="forward_vls_sam",
            requested_munition_family="vls_sam",
            authority="legacy_fire_missile",
        )

        before = kernel.debug_get_naval_weapon_counts(ddg)
        missile_id = int(kernel.fire_missile(ddg, target))
        after = kernel.debug_get_naval_weapon_counts(ddg)
        event = self._naval_launch_event(
            event_id=64104,
            request=request,
            accepted=False,
            selected_launcher=request.mount_id,
            selected_munition="",
            ammo_delta=int(after[1]) - int(before[1]),
            cooldown_delta_s=0.0,
            rejection_reason="no_active_track",
        )

        self.assertEqual(missile_id, 0)
        self.assertTrue(bool(request.has_target_entity))
        self.assertFalse(bool(request.has_target_track))
        self.assertEqual(request.target_track_id, 0)
        self.assertEqual(request.station_id, "naval:vls")
        self.assertEqual(request.mount_id, "forward_vls_sam")
        self.assertEqual(request.requested_munition_family, "vls_sam")
        self.assertEqual(request.authority, "legacy_fire_missile")

        self.assertEqual(int(before[1]), int(after[1]))
        self.assertEqual(int(before[2]), int(after[2]))
        self.assertEqual(int(before[3]), int(after[3]))
        self.assertFalse(bool(event.accepted))
        self.assertEqual(event.request_id, request.request_id)
        self.assertEqual(event.rejection_reason, "no_active_track")
        self.assertEqual(event.selected_launcher, request.mount_id)
        self.assertEqual(event.selected_munition, "")
        self.assertEqual(event.ammo_delta, 0)
        self.assertAlmostEqual(event.cooldown_delta_s, 0.0, places=6)
        self.assertFalse(bool(event.has_spawned_munition))
        self.assertEqual(event.spawned_munition.entity_id, 0)


if __name__ == "__main__":
    unittest.main()
