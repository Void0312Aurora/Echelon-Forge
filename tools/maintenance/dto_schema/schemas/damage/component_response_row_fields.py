"""Declarative DTO schema for ComponentResponseRow fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ComponentResponseRow fields.\n'
    '//\n'
    '// Consumers define EF_COMPONENT_RESPONSE_ROW_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_COMPONENT_RESPONSE_ROW_FIELD\n'
)


SCHEMA = DtoSchema(
    name='component_response_row',
    output_path='src/runtime/contracts/detail/damage/component_response_row.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='owner_stage', cpp_type='std::string', default='"component_response"', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='source_current_owner_stage', cpp_type='std::string', default='"component_response_row"', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='source_row_index', cpp_type='std::uint32_t', default='0', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='component_name', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='component_system', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='component_redundancy_group_id', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='threshold_scale', cpp_type='double', default='1.0', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability', cpp_type='double', default='0.0', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_sample', cpp_type='double', default='1.0', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_source', cpp_type='std::string', default='"none"', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_calibrated', cpp_type='bool', default='false', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_evidence_dataset_ref', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_evidence_row_id', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_evidence_source_ref', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_evidence_provenance', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_authority', cpp_type='bool', default='false', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_component_specific', cpp_type='bool', default='false', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_weapon_family', cpp_type='std::string', default='"unknown"', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_aspect_bucket', cpp_type='std::string', default='"unknown"', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_closure_bucket', cpp_type='std::string', default='"unknown"', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_miss_distance_bucket', cpp_type='std::string', default='"unknown"', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_evidence_component_name', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_evidence_component_system', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_probability_evidence_component_redundancy_group_id', cpp_type='std::string', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_mode', cpp_type='std::string', default='"none"', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_severity', cpp_type='double', default='0.0', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_mode_names', cpp_type='std::vector<std::string>', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_mode_severities', cpp_type='std::vector<double>', default='{}', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_mode_source', cpp_type='std::string', default='"none"', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='failure_mode_authority', cpp_type='bool', default='false', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='integrity_before', cpp_type='double', default='1.0', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='integrity_after', cpp_type='double', default='1.0', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='redundancy_group_availability_before', cpp_type='double', default='1.0', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
        Field(name='redundancy_group_availability_after', cpp_type='double', default='1.0', group='EF_COMPONENT_RESPONSE_ROW_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
