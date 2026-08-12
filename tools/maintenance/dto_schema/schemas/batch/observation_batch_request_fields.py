"""Declarative DTO schema for ObservationBatchRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ObservationBatchRequest fields.\n'
    '//\n'
    '// Consumers define EF_OBSERVATION_BATCH_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_OBSERVATION_BATCH_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='observation_batch_request',
    output_path='src/runtime/facade/detail/batch/observation_batch_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='refs', cpp_type='std::vector<WorldEntityRef>', default='{}', group='EF_OBSERVATION_BATCH_REQUEST_FIELD'),
        Field(name='include_agent_observations', cpp_type='bool', default='true', group='EF_OBSERVATION_BATCH_REQUEST_FIELD'),
        Field(name='include_instrument_states', cpp_type='bool', default='false', group='EF_OBSERVATION_BATCH_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
