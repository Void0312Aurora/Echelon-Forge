"""Declarative DTO schema for runtime::platform_capabilities::Capability fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of runtime::platform_capabilities::Capability fields.\n'
    '//\n'
    '// Consumers define EF_PLATFORM_CAPABILITY_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_PLATFORM_CAPABILITY_FIELD\n'
)


SCHEMA = DtoSchema(
    name='platform_capability',
    output_path='src/runtime/contracts/detail/platform/platform_capability.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='capability_id', cpp_type='std::string', default='{}', group='EF_PLATFORM_CAPABILITY_FIELD'),
        Field(name='family', cpp_type='std::string', default='{}', group='EF_PLATFORM_CAPABILITY_FIELD'),
        Field(name='capability_type', cpp_type='std::string', default='{}', group='EF_PLATFORM_CAPABILITY_FIELD'),
        Field(name='implementation_ref', cpp_type='std::string', default='{}', group='EF_PLATFORM_CAPABILITY_FIELD'),
        Field(name='requires_capability_ids', cpp_type='std::vector<std::string>', default='{}', group='EF_PLATFORM_CAPABILITY_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_PLATFORM_CAPABILITY_FIELD'),
        Field(name='required', cpp_type='bool', default='true', group='EF_PLATFORM_CAPABILITY_FIELD'),
        Field(name='supported', cpp_type='bool', default='true', group='EF_PLATFORM_CAPABILITY_FIELD'),
        Field(name='unsupported_reason', cpp_type='std::string', default='{}', group='EF_PLATFORM_CAPABILITY_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
