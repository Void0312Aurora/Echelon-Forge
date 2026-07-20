// X-macro list of MunitionLifecyclePacket fields.
//
// Consumers define EF_MUNITION_LIFECYCLE_PACKET_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_MUNITION_LIFECYCLE_PACKET_FIELD(std::uint64_t, packet_id, 0)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(EngagementEntityRef, munition, {})
EF_MUNITION_LIFECYCLE_PACKET_FIELD(EngagementEntityRef, attacker, {})
EF_MUNITION_LIFECYCLE_PACKET_FIELD(EngagementEntityRef, target_entity, {})
EF_MUNITION_LIFECYCLE_PACKET_FIELD(bool, has_target_entity, false)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(std::uint64_t, target_track_id, 0)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(bool, has_target_track, false)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(std::uint64_t, launch_event_id, 0)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(bool, active, false)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(std::string, seeker_mode, "unknown")
EF_MUNITION_LIFECYCLE_PACKET_FIELD(double, guidance_cadence_s, 0.0)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(std::string, track_memory_state, "unknown")
EF_MUNITION_LIFECYCLE_PACKET_FIELD(double, fuel_remaining_fraction, 0.0)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(bool, burnout, false)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(double, max_flight_time_s, 0.0)
EF_MUNITION_LIFECYCLE_PACKET_FIELD(std::string, fuze_state, "unknown")
EF_MUNITION_LIFECYCLE_PACKET_FIELD(double, source_time_s, 0.0)

#undef EF_MUNITION_LIFECYCLE_PACKET_FIELD
