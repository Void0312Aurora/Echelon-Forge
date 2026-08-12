"""Declarative DTO schema for TaskingBatchRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TaskingBatchRequest fields.\n'
    '//\n'
    '// Consumers define EF_TASKING_BATCH_REQUEST_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TASKING_BATCH_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='tasking_batch_request',
    output_path='src/runtime/facade/detail/batch/tasking_batch_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='refs', cpp_type='std::vector<WorldEntityRef>', default='{}', group='EF_TASKING_BATCH_REQUEST_FIELD'),
        Field(name='include_mission_command_contracts', cpp_type='bool', default='false', group='EF_TASKING_BATCH_REQUEST_FIELD'),
        Field(name='include_task_order_contracts', cpp_type='bool', default='false', group='EF_TASKING_BATCH_REQUEST_FIELD'),
        Field(name='include_leader_intent_contracts', cpp_type='bool', default='false', group='EF_TASKING_BATCH_REQUEST_FIELD'),
        Field(name='include_pilot_report_contracts', cpp_type='bool', default='false', group='EF_TASKING_BATCH_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
