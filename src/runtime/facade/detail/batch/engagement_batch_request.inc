// X-macro list of EngagementBatchRequest fields.
//
// Consumers define EF_ENGAGEMENT_BATCH_REQUEST_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_ENGAGEMENT_BATCH_REQUEST_FIELD(std::vector<EngagementEntityRef>, refs, {})
EF_ENGAGEMENT_BATCH_REQUEST_FIELD(std::vector<std::uint64_t>, trace_ids, {})
EF_ENGAGEMENT_BATCH_REQUEST_FIELD(bool, include_track_packets, true)
EF_ENGAGEMENT_BATCH_REQUEST_FIELD(bool, include_launch_requests, true)
EF_ENGAGEMENT_BATCH_REQUEST_FIELD(bool, include_launch_events, true)
EF_ENGAGEMENT_BATCH_REQUEST_FIELD(bool, include_munition_lifecycle_packets, true)
EF_ENGAGEMENT_BATCH_REQUEST_FIELD(bool, include_effects_events, true)
EF_ENGAGEMENT_BATCH_REQUEST_FIELD(bool, include_damage_reports, true)
EF_ENGAGEMENT_BATCH_REQUEST_FIELD(bool, include_diagnostics_traces, true)

#undef EF_ENGAGEMENT_BATCH_REQUEST_FIELD
