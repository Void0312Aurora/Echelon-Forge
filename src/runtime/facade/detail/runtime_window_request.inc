// X-macro list of RuntimeWindowRequest fields.
//
// Consumers define EF_RUNTIME_WINDOW_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WINDOW_REQUEST_FIELD(std::string, window_id, {})
EF_RUNTIME_WINDOW_REQUEST_FIELD(std::uint64_t, world_id, 0)
EF_RUNTIME_WINDOW_REQUEST_FIELD(double, source_time_s, 0.0)
EF_RUNTIME_WINDOW_REQUEST_FIELD(std::vector<RuntimeWindowActionRequest>, action_requests, {})
EF_RUNTIME_WINDOW_REQUEST_FIELD(ObservationBatchRequest, observation_request, {})
EF_RUNTIME_WINDOW_REQUEST_FIELD(EngagementBatchRequest, engagement_request, {})
EF_RUNTIME_WINDOW_REQUEST_FIELD(RuntimeWindowCadenceConfig, cadence_config, {})
EF_RUNTIME_WINDOW_REQUEST_FIELD(bool, export_observation, true)
EF_RUNTIME_WINDOW_REQUEST_FIELD(bool, export_engagement, true)
EF_RUNTIME_WINDOW_REQUEST_FIELD(bool, export_diagnostics, true)

#undef EF_RUNTIME_WINDOW_REQUEST_FIELD
