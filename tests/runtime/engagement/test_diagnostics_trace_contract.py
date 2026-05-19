from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402


def _entity_ref(entity_id: int, *, world_index: int = 0) -> ef_py.EngagementEntityRef:
    ref = ef_py.EngagementEntityRef()
    ref.world_index = world_index
    ref.entity_id = entity_id
    return ref


class DiagnosticsTraceContractTests(unittest.TestCase):
    def test_trace_chain_links_track_launch_munition_effects_damage_and_observation_version(self) -> None:
        shooter = _entity_ref(1101)
        target = _entity_ref(2202)
        munition = _entity_ref(3303)
        chain_id = 0xE30001

        track = ef_py.TrackPacket()
        track.track_id = 4101
        track.correlated_entity = target
        track.has_correlated_entity = True
        track.correlation_policy = "entity_id"
        track.source = "synthetic_contract"
        track.classification = "surface_combatant"
        track.status = "firm"
        track.quality = 0.95
        track.confidence = 0.9
        track.usable = True
        track.iff = "hostile"
        track.source_time_s = 12.0
        track.update_age_s = 0.1
        track.snapshot_version = 77

        request = ef_py.LaunchRequest()
        request.request_id = 5101
        request.shooter = shooter
        request.target_entity = target
        request.has_target_entity = True
        request.target_track_id = track.track_id
        request.has_target_track = True
        request.station_id = "naval:vls"
        request.mount_id = "mk41-aft"
        request.requested_munition_family = "sam"
        request.authority = "contract_test"
        request.requested_time_s = 12.2

        launch = ef_py.LaunchEvent()
        launch.event_id = 6101
        launch.request_id = request.request_id
        launch.accepted = True
        launch.selected_launcher = request.station_id
        launch.selected_munition = request.requested_munition_family
        launch.ammo_delta = -1
        launch.cooldown_delta_s = 2.5
        launch.spawned_munition = munition
        launch.has_spawned_munition = True
        launch.event_time_s = 12.25

        lifecycle = ef_py.MunitionLifecyclePacket()
        lifecycle.packet_id = 7101
        lifecycle.munition = munition
        lifecycle.attacker = shooter
        lifecycle.target_entity = target
        lifecycle.has_target_entity = True
        lifecycle.target_track_id = track.track_id
        lifecycle.has_target_track = True
        lifecycle.launch_event_id = launch.event_id
        lifecycle.active = True
        lifecycle.seeker_mode = "midcourse"
        lifecycle.guidance_cadence_s = 0.2
        lifecycle.track_memory_state = "valid"
        lifecycle.fuel_remaining_fraction = 0.8
        lifecycle.max_flight_time_s = 90.0
        lifecycle.fuze_state = "armed"
        lifecycle.source_time_s = 12.45

        effects = ef_py.EffectsEvent()
        effects.event_id = 8101
        effects.munition = munition
        effects.target = target
        effects.trigger_type = "proximity_fuze"
        effects.outcome_state = "hit"
        effects.detonation_time_s = 14.0
        effects.nearest_approach_time_s = 14.0
        effects.quality = 0.87
        effects.confidence = 0.92
        effects.effect_family = "blast_fragmentation"

        damage = ef_py.DamageReport()
        damage.report_id = 9101
        damage.target = target
        damage.source_event_id = effects.event_id
        damage.hp_delta = -35.0
        damage.system_health_delta = -0.25
        damage.platform_damage_state_delta = "sensor=-0.25"
        damage.sensor_kill = True
        damage.loss_state_from = "active"
        damage.loss_state_to = "damaged"
        damage.report_time_s = 14.1

        trace = ef_py.DiagnosticsTrace()
        trace.trace_id = 10101
        trace.parent_trace_id = 0
        trace.chain_id = chain_id
        trace.track_id = track.track_id
        trace.launch_request_id = request.request_id
        trace.launch_event_id = launch.event_id
        trace.munition = munition
        trace.effects_event_id = effects.event_id
        trace.damage_report_id = damage.report_id
        trace.observation_packet_version = track.snapshot_version

        packet = ef_py.EngagementEventPacket()
        packet.refs = [shooter, target, munition]
        packet.trace_ids = [trace.trace_id]
        packet.track_packets = [track]
        packet.launch_requests = [request]
        packet.launch_events = [launch]
        packet.munition_lifecycle_packets = [lifecycle]
        packet.effects_events = [effects]
        packet.damage_reports = [damage]
        packet.diagnostics_traces = [trace]

        self.assertEqual(list(packet.trace_ids), [trace.trace_id])
        self.assertEqual(packet.diagnostics_traces[0].chain_id, chain_id)
        self.assertEqual(packet.diagnostics_traces[0].parent_trace_id, 0)
        self.assertEqual(packet.diagnostics_traces[0].track_id, packet.track_packets[0].track_id)
        self.assertEqual(packet.launch_requests[0].target_track_id, packet.track_packets[0].track_id)
        self.assertEqual(packet.launch_events[0].request_id, packet.launch_requests[0].request_id)
        self.assertEqual(packet.munition_lifecycle_packets[0].launch_event_id, packet.launch_events[0].event_id)
        self.assertEqual(
            packet.munition_lifecycle_packets[0].munition.entity_id,
            packet.launch_events[0].spawned_munition.entity_id,
        )
        self.assertEqual(packet.effects_events[0].munition.entity_id, packet.launch_events[0].spawned_munition.entity_id)
        self.assertEqual(packet.damage_reports[0].source_event_id, packet.effects_events[0].event_id)
        self.assertEqual(packet.diagnostics_traces[0].launch_request_id, packet.launch_requests[0].request_id)
        self.assertEqual(packet.diagnostics_traces[0].launch_event_id, packet.launch_events[0].event_id)
        self.assertEqual(packet.diagnostics_traces[0].munition.entity_id, packet.launch_events[0].spawned_munition.entity_id)
        self.assertEqual(packet.diagnostics_traces[0].effects_event_id, packet.effects_events[0].event_id)
        self.assertEqual(packet.diagnostics_traces[0].damage_report_id, packet.damage_reports[0].report_id)
        self.assertEqual(packet.diagnostics_traces[0].observation_packet_version, packet.track_packets[0].snapshot_version)


if __name__ == "__main__":
    unittest.main()
