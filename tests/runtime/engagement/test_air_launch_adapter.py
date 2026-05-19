from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")


def _make_air_combat_fixture() -> tuple[ef_py.SimulationKernel, int, int]:
    sim = ef_py.SimulationKernel()
    if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")

    sim.set_time_step(0.05)
    sim.set_terrain_type("flat")
    sim.set_wind(0.0, 0.0, 0.0)

    blue_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            0.0,
            0.0,
            1200.0,
            0.0,
            0.0,
            0.0,
            0.0,
            180.0,
            0.0,
        )
    )
    red_id = int(
        sim.spawn_unit(
            ef_py.Side.Red,
            "F-16C_Block50",
            0.0,
            8000.0,
            1200.0,
            180.0,
            0.0,
            0.0,
            0.0,
            -180.0,
            0.0,
        )
    )
    sim.set_unit_ammo(blue_id, 4, 4)
    sim.set_weapon_cooldown(blue_id, 0.75, -1.0)
    return sim, blue_id, red_id


def _entity_ref(entity_id: int, *, world_index: int = 0) -> ef_py.EngagementEntityRef:
    ref = ef_py.EngagementEntityRef()
    ref.world_index = world_index
    ref.entity_id = entity_id
    return ref


def _make_air_launch_request(
    *,
    request_id: int,
    shooter_id: int,
    target_id: int,
    target_track_id: int,
    requested_time_s: float,
    world_index: int = 0,
) -> ef_py.LaunchRequest:
    request = ef_py.LaunchRequest()
    request.request_id = request_id
    request.shooter = _entity_ref(shooter_id, world_index=world_index)
    request.target_entity = _entity_ref(target_id, world_index=world_index)
    request.has_target_entity = True
    request.target_track_id = target_track_id
    request.has_target_track = True
    request.station_id = "air:pylon"
    request.requested_munition_family = "missile"
    request.authority = "legacy_fire_missile"
    request.requested_time_s = requested_time_s
    request.merge_policy = "reject_on_conflict"
    return request


def _make_air_launch_event(
    *,
    event_id: int,
    request_id: int,
    accepted: bool,
    spawned_munition_id: int,
    ammo_delta: int,
    event_time_s: float,
    rejection_reason: str = "",
    world_index: int = 0,
) -> ef_py.LaunchEvent:
    event = ef_py.LaunchEvent()
    event.event_id = event_id
    event.request_id = request_id
    event.accepted = accepted
    event.rejection_reason = rejection_reason
    event.selected_launcher = "air:pylon"
    event.selected_munition = "missile" if accepted else ""
    event.ammo_delta = ammo_delta
    event.cooldown_delta_s = 0.75 if accepted else 0.0
    event.spawned_munition = _entity_ref(spawned_munition_id, world_index=world_index)
    event.has_spawned_munition = spawned_munition_id != 0
    event.event_time_s = event_time_s
    return event


def _wait_for_track(
    sim: ef_py.SimulationKernel,
    shooter_id: int,
    target_id: int,
    *,
    max_steps: int = 80,
) -> tuple[int, float]:
    for step_index in range(1, max_steps + 1):
        sim.step()
        obs = sim.get_agent_observation(shooter_id)
        for track in getattr(obs, "contacts", []):
            track_id = int(getattr(track, "id", 0))
            if track_id == target_id:
                return track_id, step_index * float(sim.get_time_step())
    raise AssertionError(f"expected shooter {shooter_id} to acquire target track {target_id}")


class AirLaunchAdapterTests(unittest.TestCase):
    def test_accepted_legacy_fire_missile_outcome_fits_launch_request_and_event_shape(self) -> None:
        sim, blue_id, red_id = _make_air_combat_fixture()
        target_track_id, request_time_s = _wait_for_track(sim, blue_id, red_id)

        before = sim.get_agent_observation(blue_id)
        missiles_before = int(getattr(before, "missiles_remaining", -1))
        self.assertEqual(missiles_before, 4)
        self.assertTrue(bool(getattr(before, "can_fire", False)))

        request = _make_air_launch_request(
            request_id=1001,
            shooter_id=blue_id,
            target_id=red_id,
            target_track_id=target_track_id,
            requested_time_s=request_time_s,
        )

        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        after = sim.get_agent_observation(blue_id)
        missiles_after = int(getattr(after, "missiles_remaining", -1))
        event = _make_air_launch_event(
            event_id=2001,
            request_id=request.request_id,
            accepted=True,
            spawned_munition_id=missile_id,
            ammo_delta=missiles_after - missiles_before,
            event_time_s=request.requested_time_s,
        )

        self.assertEqual(request.shooter.entity_id, blue_id)
        self.assertEqual(request.target_entity.entity_id, red_id)
        self.assertTrue(bool(request.has_target_entity))
        self.assertEqual(request.target_track_id, target_track_id)
        self.assertTrue(bool(request.has_target_track))
        self.assertEqual(request.station_id, "air:pylon")
        self.assertEqual(request.requested_munition_family, "missile")
        self.assertEqual(request.authority, "legacy_fire_missile")

        self.assertTrue(bool(event.accepted))
        self.assertEqual(event.request_id, request.request_id)
        self.assertEqual(event.rejection_reason, "")
        self.assertEqual(event.selected_launcher, request.station_id)
        self.assertEqual(event.selected_munition, request.requested_munition_family)
        self.assertEqual(event.ammo_delta, -1)
        self.assertAlmostEqual(event.cooldown_delta_s, 0.75)
        self.assertTrue(bool(event.has_spawned_munition))
        self.assertEqual(event.spawned_munition.entity_id, missile_id)
        self.assertEqual(missiles_after, 3)
        self.assertFalse(bool(getattr(after, "can_fire", True)))

    def test_rejected_legacy_fire_missile_without_track_fits_rejected_launch_event_shape(self) -> None:
        sim, blue_id, red_id = _make_air_combat_fixture()
        before = sim.get_agent_observation(blue_id)
        missiles_before = int(getattr(before, "missiles_remaining", -1))

        request = _make_air_launch_request(
            request_id=1002,
            shooter_id=blue_id,
            target_id=red_id,
            target_track_id=0,
            requested_time_s=0.0,
        )
        request.has_target_track = False

        missile_id = int(sim.fire_missile(blue_id, red_id))
        self.assertEqual(missile_id, 0)

        after = sim.get_agent_observation(blue_id)
        missiles_after = int(getattr(after, "missiles_remaining", -1))
        event = _make_air_launch_event(
            event_id=2002,
            request_id=request.request_id,
            accepted=False,
            spawned_munition_id=missile_id,
            ammo_delta=missiles_after - missiles_before,
            event_time_s=request.requested_time_s,
            rejection_reason="no_active_track",
        )

        self.assertTrue(bool(request.has_target_entity))
        self.assertFalse(bool(request.has_target_track))
        self.assertFalse(bool(event.accepted))
        self.assertEqual(event.request_id, request.request_id)
        self.assertEqual(event.rejection_reason, "no_active_track")
        self.assertEqual(event.ammo_delta, 0)
        self.assertEqual(event.cooldown_delta_s, 0.0)
        self.assertFalse(bool(event.has_spawned_munition))
        self.assertEqual(event.spawned_munition.entity_id, 0)
        self.assertEqual(missiles_after, missiles_before)
        self.assertTrue(bool(getattr(after, "can_fire", False)))


if __name__ == "__main__":
    unittest.main()
