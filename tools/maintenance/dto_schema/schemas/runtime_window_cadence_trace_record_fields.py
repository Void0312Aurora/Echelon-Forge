"""Declarative DTO schema for RuntimeWindowCadenceTraceRecord fields.

The Python binding has long registered these properties alphabetically
rather than in declaration order, so only the C++ struct side is expanded
from this schema; the binding's ``def_rw`` block stays hand-written (see
the I26 sub-family report for the recorded partial-coverage rationale).
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowCadenceTraceRecord fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    '// #undef\'d here after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_cadence_trace_record',
    output_path='src/runtime/facade/detail/runtime_window_cadence_trace_record.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='domain', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='tick', cpp_type='std::uint32_t', default='0', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='node_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='decision', cpp_type='std::string', default='"skipped"', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='decision_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='source', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='barrier_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='clock_domain', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='clock_merge_policy', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='cadence_merge_policy', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='relation', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='held', cpp_type='bool', default='false', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='expired', cpp_type='bool', default='false', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='deferred', cpp_type='bool', default='false', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
        Field(name='diagnostics_only', cpp_type='bool', default='false', group='EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
