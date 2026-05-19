from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


def public_fields(instance: object) -> tuple[str, ...]:
    return tuple(name for name in dir(instance) if not name.startswith("_"))


class BindingsEngagementSurfaceTests(unittest.TestCase):
    def test_engagement_entity_ref_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.EngagementEntityRef()),
            (
                "entity_id",
                "world_index",
            ),
        )

    def test_track_packet_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.TrackPacket()),
            (
                "classification",
                "confidence",
                "correlated_entity",
                "correlation_policy",
                "has_correlated_entity",
                "iff",
                "quality",
                "snapshot_version",
                "source",
                "source_time_s",
                "status",
                "track_id",
                "update_age_s",
                "usable",
            ),
        )

    def test_launch_request_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.LaunchRequest()),
            (
                "authority",
                "has_target_entity",
                "has_target_track",
                "merge_policy",
                "mount_id",
                "request_id",
                "requested_munition_family",
                "requested_time_s",
                "shooter",
                "station_id",
                "target_entity",
                "target_track_id",
            ),
        )

    def test_launch_event_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.LaunchEvent()),
            (
                "accepted",
                "ammo_delta",
                "cooldown_delta_s",
                "event_id",
                "event_time_s",
                "has_spawned_munition",
                "rejection_reason",
                "request_id",
                "selected_launcher",
                "selected_munition",
                "spawned_munition",
            ),
        )

    def test_munition_lifecycle_packet_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.MunitionLifecyclePacket()),
            (
                "active",
                "attacker",
                "burnout",
                "fuel_remaining_fraction",
                "fuze_state",
                "guidance_cadence_s",
                "has_target_entity",
                "has_target_track",
                "launch_event_id",
                "max_flight_time_s",
                "munition",
                "packet_id",
                "seeker_mode",
                "source_time_s",
                "target_entity",
                "target_track_id",
                "track_memory_state",
            ),
        )

    def test_effects_event_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.EffectsEvent()),
            (
                "confidence",
                "detonation_time_s",
                "effect_family",
                "event_id",
                "munition",
                "nearest_approach_time_s",
                "outcome_state",
                "quality",
                "target",
                "trigger_type",
            ),
        )

    def test_damage_report_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.DamageReport()),
            (
                "destroyed",
                "hp_delta",
                "loss_state_from",
                "loss_state_to",
                "mission_kill",
                "mobility_kill",
                "platform_damage_state_delta",
                "report_id",
                "report_time_s",
                "sensor_kill",
                "source_event_id",
                "survivability_kill",
                "system_health_delta",
                "target",
            ),
        )

    def test_diagnostics_trace_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.DiagnosticsTrace()),
            (
                "chain_id",
                "damage_report_id",
                "effects_event_id",
                "launch_event_id",
                "launch_request_id",
                "munition",
                "observation_packet_version",
                "parent_trace_id",
                "trace_id",
                "track_id",
            ),
        )

    def test_engagement_batch_request_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.EngagementBatchRequest()),
            (
                "include_damage_reports",
                "include_diagnostics_traces",
                "include_effects_events",
                "include_launch_events",
                "include_launch_requests",
                "include_munition_lifecycle_packets",
                "include_track_packets",
                "refs",
                "trace_ids",
            ),
        )

    def test_engagement_event_packet_public_fields_match_expected_binding_surface(self) -> None:
        self.assertTupleEqual(
            public_fields(ef_py.EngagementEventPacket()),
            (
                "damage_reports",
                "diagnostics_traces",
                "effects_events",
                "launch_events",
                "launch_requests",
                "munition_lifecycle_packets",
                "refs",
                "trace_ids",
                "track_packets",
            ),
        )

    def test_defaults_are_exposed_for_engagement_dtos(self) -> None:
        track = ef_py.TrackPacket()
        self.assertEqual(track.correlation_policy, "unresolved")
        self.assertEqual(track.classification, "unknown")
        self.assertEqual(track.status, "unknown")
        self.assertFalse(bool(track.usable))

        request = ef_py.LaunchRequest()
        self.assertEqual(request.authority, "unspecified")
        self.assertEqual(request.merge_policy, "reject_on_conflict")

    def test_nested_entity_ref_round_trips_through_dto_fields(self) -> None:
        ref = ef_py.EngagementEntityRef()
        ref.world_index = 3
        ref.entity_id = 42

        event = ef_py.LaunchEvent()
        event.event_id = 7
        event.accepted = True
        event.spawned_munition = ref
        event.has_spawned_munition = True

        self.assertEqual(event.event_id, 7)
        self.assertTrue(bool(event.accepted))
        self.assertTrue(bool(event.has_spawned_munition))
        self.assertEqual(event.spawned_munition.world_index, 3)
        self.assertEqual(event.spawned_munition.entity_id, 42)

    def test_runtime_facade_exports_empty_engagement_packet_shell(self) -> None:
        ref = ef_py.EngagementEntityRef()
        ref.world_index = 2
        ref.entity_id = 9001

        request = ef_py.EngagementBatchRequest()
        request.refs = [ref]
        request.trace_ids = [1234]

        packet = ef_py.RuntimeFacade(1).export_engagement_event_packet(request)

        self.assertEqual(len(packet.refs), 1)
        self.assertEqual(packet.refs[0].world_index, 2)
        self.assertEqual(packet.refs[0].entity_id, 9001)
        self.assertEqual(list(packet.trace_ids), [1234])
        self.assertEqual(list(packet.track_packets), [])
        self.assertEqual(list(packet.launch_requests), [])
        self.assertEqual(list(packet.launch_events), [])
        self.assertEqual(list(packet.munition_lifecycle_packets), [])
        self.assertEqual(list(packet.effects_events), [])
        self.assertEqual(list(packet.damage_reports), [])
        self.assertEqual(list(packet.diagnostics_traces), [])


if __name__ == "__main__":
    unittest.main()
