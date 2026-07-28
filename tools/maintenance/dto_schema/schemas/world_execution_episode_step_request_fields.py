"""Declarative DTO schema for WorldExecutionEpisodeStepRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of WorldExecutionEpisodeStepRequest fields.\n'
    '//\n'
    '// Consumers define EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    '// #undef\'d here after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='world_execution_episode_step_request',
    output_path='src/runtime/contracts/detail/world_execution_episode_step_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD'),
        Field(name='entity_id', cpp_type='std::uint64_t', default='0', group='EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD'),
        Field(name='config', cpp_type='StepEvaluationBatchConfig', default='{}', group='EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD'),
        Field(name='env_state', cpp_type='StepEvaluationBatchEnvState', default='{}', group='EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
