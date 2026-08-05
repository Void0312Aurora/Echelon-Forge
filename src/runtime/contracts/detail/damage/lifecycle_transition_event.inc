// X-macro list of LifecycleTransitionEvent fields.
//
// Consumers define EF_LIFECYCLE_TRANSITION_EVENT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_LIFECYCLE_TRANSITION_EVENT_FIELD(LethalityChainHeader, header, {})
EF_LIFECYCLE_TRANSITION_EVENT_FIELD(std::string, lifecycle_from, "unknown")
EF_LIFECYCLE_TRANSITION_EVENT_FIELD(std::string, lifecycle_to, "unknown")
EF_LIFECYCLE_TRANSITION_EVENT_FIELD(std::string, ground_lifecycle, "unknown")
EF_LIFECYCLE_TRANSITION_EVENT_FIELD(EngagementEntityRef, wreck_entity, {})
EF_LIFECYCLE_TRANSITION_EVENT_FIELD(std::uint32_t, debris_count, 0)
EF_LIFECYCLE_TRANSITION_EVENT_FIELD(bool, terminal, false)
EF_LIFECYCLE_TRANSITION_EVENT_FIELD(std::uint64_t, terminal_projection_id, 0)

#undef EF_LIFECYCLE_TRANSITION_EVENT_FIELD
