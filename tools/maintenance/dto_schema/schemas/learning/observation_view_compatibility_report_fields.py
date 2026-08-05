"""Declarative DTO schema for ObservationViewCompatibilityReport fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ObservationViewCompatibilityReport fields.\n'
    '//\n'
    '// Consumers define EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='observation_view_compatibility_report',
    output_path='src/runtime/contracts/detail/learning/observation_view_compatibility_report.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='compatible', cpp_type='bool', default='false', group='EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD'),
        Field(name='major_compatible', cpp_type='bool', default='false', group='EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD'),
        Field(name='required_fields_satisfied', cpp_type='bool', default='false', group='EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD'),
        Field(name='optional_field_drift_allowed', cpp_type='bool', default='false', group='EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD'),
        Field(name='missing_required_fields', cpp_type='std::vector<std::string>', default='{}', group='EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD'),
        Field(name='unknown_optional_fields', cpp_type='std::vector<std::string>', default='{}', group='EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD'),
        Field(name='missing_optional_fields', cpp_type='std::vector<std::string>', default='{}', group='EF_OBSERVATION_VIEW_COMPATIBILITY_REPORT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
