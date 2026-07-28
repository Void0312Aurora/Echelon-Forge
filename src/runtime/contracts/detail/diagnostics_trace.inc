// X-macro list of DiagnosticsTrace fields.
//
// Consumers define EF_DIAGNOSTICS_TRACE_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, trace_id, 0)
EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, parent_trace_id, 0)
EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, chain_id, 0)
EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, track_id, 0)
EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, launch_request_id, 0)
EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, launch_event_id, 0)
EF_DIAGNOSTICS_TRACE_FIELD(EngagementEntityRef, munition, {})
EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, effects_event_id, 0)
EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, damage_report_id, 0)
EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, observation_packet_version, 0)
EF_DIAGNOSTICS_TRACE_FIELD(std::uint64_t, source_snapshot_version, 0)
EF_DIAGNOSTICS_TRACE_FIELD(std::string, barrier_id, "export")
EF_DIAGNOSTICS_TRACE_FIELD(std::string, barrier_detail, "maintained_facade_export")
EF_DIAGNOSTICS_TRACE_FIELD(double, source_time_s, 0.0)
EF_DIAGNOSTICS_TRACE_FIELD(std::string, source_node_id, {})
EF_DIAGNOSTICS_TRACE_FIELD(std::string, export_node_id, {})

#undef EF_DIAGNOSTICS_TRACE_FIELD
