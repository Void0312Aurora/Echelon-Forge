"""Declarative DTO schema for EngagementEntityRef fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of EngagementEntityRef fields.\n'
    '//\n'
    '// Consumers define EF_ENGAGEMENT_ENTITY_REF_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_ENGAGEMENT_ENTITY_REF_FIELD\n'
)


SCHEMA = DtoSchema(
    name='engagement_entity_ref',
    output_path='src/runtime/contracts/detail/engagement_entity_ref.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_ENGAGEMENT_ENTITY_REF_FIELD'),
        Field(name='entity_id', cpp_type='std::uint64_t', default='0', group='EF_ENGAGEMENT_ENTITY_REF_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
