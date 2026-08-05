// X-macro list of LaunchEvent fields.
//
// Consumers define EF_LAUNCH_EVENT_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_LAUNCH_EVENT_FIELD(std::uint64_t, event_id, 0)
EF_LAUNCH_EVENT_FIELD(std::uint64_t, request_id, 0)
EF_LAUNCH_EVENT_FIELD(bool, accepted, false)
EF_LAUNCH_EVENT_FIELD(std::string, rejection_reason, {})
EF_LAUNCH_EVENT_FIELD(std::string, selected_launcher, {})
EF_LAUNCH_EVENT_FIELD(std::string, selected_munition, {})
EF_LAUNCH_EVENT_FIELD(int, ammo_delta, 0)
EF_LAUNCH_EVENT_FIELD(double, cooldown_delta_s, 0.0)
EF_LAUNCH_EVENT_FIELD(EngagementEntityRef, spawned_munition, {})
EF_LAUNCH_EVENT_FIELD(bool, has_spawned_munition, false)
EF_LAUNCH_EVENT_FIELD(double, event_time_s, 0.0)
EF_LAUNCH_EVENT_FIELD(std::string, producer_node_id, {})

#undef EF_LAUNCH_EVENT_FIELD
