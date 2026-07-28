// X-macro list of RuntimeWindowCadenceConfig fields.
//
// Consumers define EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD(double, window_duration_s, 0.0)
EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD(std::vector<RuntimeWindowCadence>, domains, {})

#undef EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD
