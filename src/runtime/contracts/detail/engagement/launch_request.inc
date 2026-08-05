// X-macro list of LaunchRequest fields.
//
// Consumers define EF_LAUNCH_REQUEST_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_LAUNCH_REQUEST_FIELD(std::uint64_t, request_id, 0)
EF_LAUNCH_REQUEST_FIELD(EngagementEntityRef, shooter, {})
EF_LAUNCH_REQUEST_FIELD(EngagementEntityRef, target_entity, {})
EF_LAUNCH_REQUEST_FIELD(bool, has_target_entity, false)
EF_LAUNCH_REQUEST_FIELD(std::uint64_t, target_track_id, 0)
EF_LAUNCH_REQUEST_FIELD(bool, has_target_track, false)
EF_LAUNCH_REQUEST_FIELD(std::string, station_id, {})
EF_LAUNCH_REQUEST_FIELD(std::string, mount_id, {})
EF_LAUNCH_REQUEST_FIELD(std::string, requested_munition_family, {})
EF_LAUNCH_REQUEST_FIELD(std::string, authority, "unspecified")
EF_LAUNCH_REQUEST_FIELD(double, requested_time_s, 0.0)
EF_LAUNCH_REQUEST_FIELD(std::string, merge_policy, "reject_on_conflict")

#undef EF_LAUNCH_REQUEST_FIELD
