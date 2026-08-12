// X-macro list of RuntimeWindowCadence fields.
//
// Consumers define EF_RUNTIME_WINDOW_CADENCE_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WINDOW_CADENCE_FIELD(std::string, domain, "control")
EF_RUNTIME_WINDOW_CADENCE_FIELD(std::uint32_t, tick_count, 1)
EF_RUNTIME_WINDOW_CADENCE_FIELD(double, interval_s, 0.0)
EF_RUNTIME_WINDOW_CADENCE_FIELD(std::string, merge_policy, "nested_slot")
EF_RUNTIME_WINDOW_CADENCE_FIELD(std::string, barrier_id, {})

#undef EF_RUNTIME_WINDOW_CADENCE_FIELD
