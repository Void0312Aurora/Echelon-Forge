// X-macro list of TrackPacket fields.
//
// Consumers define EF_TRACK_PACKET_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_TRACK_PACKET_FIELD(std::uint64_t, track_id, 0)
EF_TRACK_PACKET_FIELD(EngagementEntityRef, correlated_entity, {})
EF_TRACK_PACKET_FIELD(bool, has_correlated_entity, false)
EF_TRACK_PACKET_FIELD(std::string, correlation_policy, "unresolved")
EF_TRACK_PACKET_FIELD(std::string, source, {})
EF_TRACK_PACKET_FIELD(std::string, classification, "unknown")
EF_TRACK_PACKET_FIELD(std::string, status, "unknown")
EF_TRACK_PACKET_FIELD(double, quality, 0.0)
EF_TRACK_PACKET_FIELD(double, confidence, 0.0)
EF_TRACK_PACKET_FIELD(bool, usable, false)
EF_TRACK_PACKET_FIELD(std::string, iff, "unknown")
EF_TRACK_PACKET_FIELD(double, source_time_s, 0.0)
EF_TRACK_PACKET_FIELD(double, update_age_s, 0.0)
EF_TRACK_PACKET_FIELD(std::uint64_t, snapshot_version, 0)

#undef EF_TRACK_PACKET_FIELD
