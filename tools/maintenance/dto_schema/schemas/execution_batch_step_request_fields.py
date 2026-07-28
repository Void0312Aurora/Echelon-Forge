"""Declarative DTO schema for ExecutionBatchStepRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ExecutionBatchStepRequest fields.\n'
    '//\n'
    '// Consumers define EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_EXECUTION_BATCH_STEP_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='execution_batch_step_request',
    output_path='src/runtime/facade/detail/execution_batch_step_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='step_requests', cpp_type='std::vector<WorldExecutionEpisodeStepRequest>', default='{}', group='EF_EXECUTION_BATCH_STEP_REQUEST_FIELD'),
        Field(name='include_agent_observations', cpp_type='bool', default='true', group='EF_EXECUTION_BATCH_STEP_REQUEST_FIELD'),
        Field(name='include_instrument_states', cpp_type='bool', default='false', group='EF_EXECUTION_BATCH_STEP_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
