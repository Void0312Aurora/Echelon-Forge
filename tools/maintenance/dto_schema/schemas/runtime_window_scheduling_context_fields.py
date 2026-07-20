"""Declarative DTO schema for RuntimeWindowSchedulingContext fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowSchedulingContext fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_scheduling_context',
    output_path='src/runtime/facade/detail/runtime_window_scheduling_context.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='window_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD'),
        Field(name='world_id', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD'),
        Field(name='barrier_sequence', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD'),
        Field(name='current_barrier_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD'),
        Field(name='accepted_inputs', cpp_type='std::vector<RuntimeWindowInputRecord>', default='{}', group='EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD'),
        Field(name='deferred_inputs', cpp_type='std::vector<RuntimeWindowInputRecord>', default='{}', group='EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD'),
        Field(name='rejected_inputs', cpp_type='std::vector<RuntimeWindowInputRecord>', default='{}', group='EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD'),
        Field(name='expired_inputs', cpp_type='std::vector<RuntimeWindowInputRecord>', default='{}', group='EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
