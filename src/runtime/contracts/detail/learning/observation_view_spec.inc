// X-macro list of ObservationViewSpec fields.
//
// Consumers define EF_OBSERVATION_VIEW_SPEC_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_OBSERVATION_VIEW_SPEC_FIELD(std::string, schema_version, "1.0")
EF_OBSERVATION_VIEW_SPEC_FIELD(std::vector<std::string>, required_fields, {})
EF_OBSERVATION_VIEW_SPEC_FIELD(std::vector<std::string>, optional_fields, {})
EF_OBSERVATION_VIEW_SPEC_FIELD(bool, reject_major_mismatch, true)
EF_OBSERVATION_VIEW_SPEC_FIELD(bool, allow_minor_version_drift, true)
EF_OBSERVATION_VIEW_SPEC_FIELD(bool, allow_unknown_optional_fields, true)
EF_OBSERVATION_VIEW_SPEC_FIELD(bool, allow_missing_optional_fields, true)
EF_OBSERVATION_VIEW_SPEC_FIELD(std::string, view_id, "")
EF_OBSERVATION_VIEW_SPEC_FIELD(std::vector<std::string>, information_layer_produced, {})
EF_OBSERVATION_VIEW_SPEC_FIELD(std::vector<std::string>, information_layer_consumed, {})
EF_OBSERVATION_VIEW_SPEC_FIELD(std::vector<std::string>, semantic_stage, {})

#undef EF_OBSERVATION_VIEW_SPEC_FIELD
