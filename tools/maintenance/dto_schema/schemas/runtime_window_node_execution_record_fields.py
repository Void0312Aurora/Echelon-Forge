"""Declarative DTO schema for RuntimeWindowNodeExecutionRecord fields.

The Python binding has long registered these properties alphabetically
rather than in declaration order, so only the C++ struct side is expanded
from this schema; the binding's ``def_rw`` block stays hand-written (see
the I26 sub-family report for the recorded partial-coverage rationale).
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowNodeExecutionRecord fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    '// #undef\'d here after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_node_execution_record',
    output_path='src/runtime/facade/detail/runtime_window_node_execution_record.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='node_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='clock_domain', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='read_snapshot_policy', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='write_commit_policy', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='visible_input_count', cpp_type='std::size_t', default='0', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='execution_state', cpp_type='std::string', default='"skipped"', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='decision_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='trigger_source', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='decision_barrier_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='clock_merge_policy', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='source_snapshot_version', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='target_window_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
        Field(name='barrier_order', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
