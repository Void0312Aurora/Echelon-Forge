// X-macro list of RuntimeWindowActionRequest::CadenceControl fields.
//
// Consumers define EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(ActionHoldPolicy, hold_policy, {})
EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(bool, enabled, false)
EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(bool, has_expiry_time, false)
EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(double, expiry_time_s, 0.0)
EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(std::string, source_cadence_domain, "control")
EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(std::uint32_t, source_tick, 0)

#undef EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD
