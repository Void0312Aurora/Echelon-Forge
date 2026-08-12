"""Declarative DTO schema for runtime::platform_capabilities::CapabilityBundle fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of runtime::platform_capabilities::CapabilityBundle fields.\n'
    '//\n'
    '// Consumers define EF_CAPABILITY_BUNDLE_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_CAPABILITY_BUNDLE_FIELD\n'
)


SCHEMA = DtoSchema(
    name='capability_bundle',
    output_path='src/runtime/contracts/detail/platform/capability_bundle.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='bundle_id', cpp_type='std::string', default='{}', group='EF_CAPABILITY_BUNDLE_FIELD'),
        Field(name='source_type_name', cpp_type='std::string', default='{}', group='EF_CAPABILITY_BUNDLE_FIELD'),
        Field(name='capabilities', cpp_type='std::vector<Capability>', default='{}', group='EF_CAPABILITY_BUNDLE_FIELD'),
        Field(name='template_evidence_ref', cpp_type='std::string', default='{}', group='EF_CAPABILITY_BUNDLE_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_CAPABILITY_BUNDLE_FIELD'),
        Field(name='type_name_projection_preserved', cpp_type='bool', default='true', group='EF_CAPABILITY_BUNDLE_FIELD'),
        Field(name='diagnostics_reason', cpp_type='std::string', default='{}', group='EF_CAPABILITY_BUNDLE_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
