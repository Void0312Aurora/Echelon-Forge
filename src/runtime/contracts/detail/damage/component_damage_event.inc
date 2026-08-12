// X-macro list of ComponentDamageEvent fields.
//
// Consumers define EF_COMPONENT_DAMAGE_EVENT_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_COMPONENT_DAMAGE_EVENT_FIELD(LethalityChainHeader, header, {})
EF_COMPONENT_DAMAGE_EVENT_FIELD(std::string, component_name, {})
EF_COMPONENT_DAMAGE_EVENT_FIELD(std::string, component_system, {})
EF_COMPONENT_DAMAGE_EVENT_FIELD(std::string, component_redundancy_group_id, {})
EF_COMPONENT_DAMAGE_EVENT_FIELD(double, integrity_before, 1.0)
EF_COMPONENT_DAMAGE_EVENT_FIELD(double, integrity_after, 1.0)
EF_COMPONENT_DAMAGE_EVENT_FIELD(std::string, failure_mode, "none")
EF_COMPONENT_DAMAGE_EVENT_FIELD(double, failure_severity, 0.0)
EF_COMPONENT_DAMAGE_EVENT_FIELD(double, failure_probability, 0.0)
EF_COMPONENT_DAMAGE_EVENT_FIELD(double, failure_sample, 1.0)

#undef EF_COMPONENT_DAMAGE_EVENT_FIELD
