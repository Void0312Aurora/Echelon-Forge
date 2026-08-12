"""Declarative DTO schema for LifecycleTransitionEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of LifecycleTransitionEvent fields.\n'
    '//\n'
    '// Consumers define EF_LIFECYCLE_TRANSITION_EVENT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_LIFECYCLE_TRANSITION_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='lifecycle_transition_event',
    output_path='src/runtime/contracts/detail/damage/lifecycle_transition_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_LIFECYCLE_TRANSITION_EVENT_FIELD'),
        Field(name='lifecycle_from', cpp_type='std::string', default='"unknown"', group='EF_LIFECYCLE_TRANSITION_EVENT_FIELD'),
        Field(name='lifecycle_to', cpp_type='std::string', default='"unknown"', group='EF_LIFECYCLE_TRANSITION_EVENT_FIELD'),
        Field(name='ground_lifecycle', cpp_type='std::string', default='"unknown"', group='EF_LIFECYCLE_TRANSITION_EVENT_FIELD'),
        Field(name='wreck_entity', cpp_type='EngagementEntityRef', default='{}', group='EF_LIFECYCLE_TRANSITION_EVENT_FIELD'),
        Field(name='debris_count', cpp_type='std::uint32_t', default='0', group='EF_LIFECYCLE_TRANSITION_EVENT_FIELD'),
        Field(name='terminal', cpp_type='bool', default='false', group='EF_LIFECYCLE_TRANSITION_EVENT_FIELD'),
        Field(name='terminal_projection_id', cpp_type='std::uint64_t', default='0', group='EF_LIFECYCLE_TRANSITION_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
