// X-macro list of ObservationViewCompatibilityReport fields.
//
// Consumers define EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(bool, compatible, false)
EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(bool, major_compatible, false)
EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(bool, required_fields_satisfied, false)
EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(bool, optional_field_drift_allowed, false)
EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(std::vector<std::string>, missing_required_fields, {})
EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(std::vector<std::string>, unknown_optional_fields, {})
EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(std::vector<std::string>, missing_optional_fields, {})

#undef EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD
