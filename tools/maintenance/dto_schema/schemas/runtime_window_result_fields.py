"""Declarative DTO schema for RuntimeWindowResult fields.

The Python binding has long registered ``cadence_config``/``cadence_trace``
immediately after ``barrier_trace`` -- ahead of ``visibility_trace`` and
``executed_nodes`` -- which differs from the header's declaration order,
so only the C++ struct side is expanded from this schema; the binding's
``def_rw`` block stays hand-written (see the I26 sub-family report for the
recorded partial-coverage rationale).
"""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWindowResult fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WINDOW_RESULT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WINDOW_RESULT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_window_result',
    output_path='src/runtime/facade/detail/runtime_window_result.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='context', cpp_type='RuntimeWindowSchedulingContext', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
        Field(name='barrier_trace', cpp_type='std::vector<RuntimeWindowBarrierRecord>', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
        Field(name='visibility_trace', cpp_type='std::vector<RuntimeWindowVisibilityRecord>', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
        Field(name='executed_nodes', cpp_type='std::vector<RuntimeWindowNodeExecutionRecord>', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
        Field(name='cadence_config', cpp_type='RuntimeWindowCadenceConfig', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
        Field(name='cadence_trace', cpp_type='std::vector<RuntimeWindowCadenceTraceRecord>', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
        Field(name='injected_inputs', cpp_type='std::vector<RuntimeWindowInputRecord>', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
        Field(name='observation_packet', cpp_type='ObservationBatchPacket', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
        Field(name='engagement_packet', cpp_type='EngagementEventPacket', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
        Field(name='diagnostics_traces', cpp_type='std::vector<DiagnosticsTrace>', default='{}', group='EF_RUNTIME_WINDOW_RESULT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
