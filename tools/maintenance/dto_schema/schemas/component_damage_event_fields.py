"""Declarative DTO schema for ComponentDamageEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ComponentDamageEvent fields.\n'
    '//\n'
    '// Consumers define EF_COMPONENT_DAMAGE_EVENT_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_COMPONENT_DAMAGE_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='component_damage_event',
    output_path='src/runtime/contracts/detail/component_damage_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
        Field(name='component_name', cpp_type='std::string', default='{}', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
        Field(name='component_system', cpp_type='std::string', default='{}', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
        Field(name='component_redundancy_group_id', cpp_type='std::string', default='{}', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
        Field(name='integrity_before', cpp_type='double', default='1.0', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
        Field(name='integrity_after', cpp_type='double', default='1.0', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
        Field(name='failure_mode', cpp_type='std::string', default='"none"', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
        Field(name='failure_severity', cpp_type='double', default='0.0', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
        Field(name='failure_probability', cpp_type='double', default='0.0', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
        Field(name='failure_sample', cpp_type='double', default='1.0', group='EF_COMPONENT_DAMAGE_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
