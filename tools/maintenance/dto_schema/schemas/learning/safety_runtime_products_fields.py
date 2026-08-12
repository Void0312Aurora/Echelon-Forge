"""Declarative DTO schema for SafetyRuntimeProducts fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of SafetyRuntimeProducts fields.\n'
    '//\n'
    '// Consumers define EF_SAFETY_PRODUCT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '// Expansion sites: struct definition (termination_runtime.h) and\n'
    '// SafetyRuntimeProducts Python bindings (bindings_episode.cpp).\n'
    '//\n'
    '// Field order is load-bearing: it fixes the member layout of the struct.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_SAFETY_PRODUCT\n'
)


SCHEMA = DtoSchema(
    name='safety_runtime_products',
    output_path='src/core/mission/runtime/detail/safety_runtime_products.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='valid', cpp_type='bool', default='false', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='early_return', cpp_type='bool', default='false', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='terminated', cpp_type='bool', default='false', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='status_flag', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='reason_code', cpp_type='TerminationReasonCode', default='TerminationReasonCode::Running', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='survival', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='crash_penalty', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='nan_guard_marker', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='stall_penalty', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='overload_penalty', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='failfast_penalty', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='gear_collapse_penalty', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='off_runway_penalty', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='gear_stress_penalty', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
        Field(name='off_runway_terminate_penalty', cpp_type='double', default='0.0', group='EF_SAFETY_PRODUCT', readonly=True),
    ),
    file_footer=FILE_FOOTER,
)
