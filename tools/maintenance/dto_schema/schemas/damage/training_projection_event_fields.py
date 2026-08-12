"""Declarative DTO schema for TrainingProjectionEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TrainingProjectionEvent fields.\n'
    '//\n'
    '// Consumers define EF_TRAINING_PROJECTION_EVENT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TRAINING_PROJECTION_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='training_projection_event',
    output_path='src/runtime/contracts/detail/damage/training_projection_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_TRAINING_PROJECTION_EVENT_FIELD'),
        Field(name='consumed_event_ids', cpp_type='std::vector<std::uint64_t>', default='{}', group='EF_TRAINING_PROJECTION_EVENT_FIELD'),
        Field(name='consumer_node_id', cpp_type='std::string', default='{}', group='EF_TRAINING_PROJECTION_EVENT_FIELD'),
        Field(name='consumer_version', cpp_type='std::string', default='{}', group='EF_TRAINING_PROJECTION_EVENT_FIELD'),
        Field(name='projection_kind', cpp_type='std::string', default='"training_consumer"', group='EF_TRAINING_PROJECTION_EVENT_FIELD'),
        Field(name='reward_term', cpp_type='std::string', default='{}', group='EF_TRAINING_PROJECTION_EVENT_FIELD'),
        Field(name='reward_delta', cpp_type='double', default='0.0', group='EF_TRAINING_PROJECTION_EVENT_FIELD'),
        Field(name='terminal_reason', cpp_type='std::string', default='{}', group='EF_TRAINING_PROJECTION_EVENT_FIELD'),
        Field(name='fact_source', cpp_type='bool', default='false', group='EF_TRAINING_PROJECTION_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
