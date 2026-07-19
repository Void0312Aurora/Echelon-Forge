"""Declarative DTO schema for SafetyRuntimeInputs fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of SafetyRuntimeInputs fields.\n'
    '//\n'
    '// Consumers define EF_SAFETY_INPUT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '// Expansion sites: struct definition (termination_runtime.h) and\n'
    '// SafetyRuntimeInputs Python bindings (bindings_episode.cpp).\n'
    '//\n'
    '// Field order is load-bearing: it fixes the member layout of the struct.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_SAFETY_INPUT\n'
)


SCHEMA = DtoSchema(
    name='safety_runtime_inputs',
    output_path='src/core/mission/runtime/detail/safety_runtime_inputs.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='finite_state_valid', cpp_type='bool', default='true', group='EF_SAFETY_INPUT'),
        Field(name='crash_penalty', cpp_type='double', default='-1000.0', group='EF_SAFETY_INPUT'),
        Field(name='survival_reward', cpp_type='double', default='0.01', group='EF_SAFETY_INPUT'),
        Field(name='health', cpp_type='double', default='100.0', group='EF_SAFETY_INPUT'),
        Field(name='airborne', cpp_type='bool', default='false', group='EF_SAFETY_INPUT'),
        Field(name='aoa_valid', cpp_type='bool', default='false', group='EF_SAFETY_INPUT'),
        Field(name='aoa_abs_deg', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='stall_threshold_deg', cpp_type='double', default='15.0', group='EF_SAFETY_INPUT'),
        Field(name='stall_penalty_weight', cpp_type='double', default='-1.0', group='EF_SAFETY_INPUT'),
        Field(name='stall_penalty_clip', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='g_abs', cpp_type='double', default='1.0', group='EF_SAFETY_INPUT'),
        Field(name='overload_g_threshold', cpp_type='double', default='6.0', group='EF_SAFETY_INPUT'),
        Field(name='overload_penalty_weight', cpp_type='double', default='-1.0', group='EF_SAFETY_INPUT'),
        Field(name='overload_penalty_clip', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='curr_alt_agl_m', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='overload_min_alt_agl_m', cpp_type='double', default='5.0', group='EF_SAFETY_INPUT'),
        Field(name='altitude_m', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='roll_abs_deg', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='pitch_abs_deg', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='failfast_penalty', cpp_type='double', default='-50.0', group='EF_SAFETY_INPUT'),
        Field(name='gear_collapsed', cpp_type='bool', default='false', group='EF_SAFETY_INPUT'),
        Field(name='gear_collapse_penalty', cpp_type='double', default='-500.0', group='EF_SAFETY_INPUT'),
        Field(name='runway_surface_phase', cpp_type='bool', default='false', group='EF_SAFETY_INPUT'),
        Field(name='on_runway_task', cpp_type='bool', default='true', group='EF_SAFETY_INPUT'),
        Field(name='gear_stress', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='gear_stress_penalty_weight', cpp_type='double', default='-10.0', group='EF_SAFETY_INPUT'),
        Field(name='off_runway_penalty', cpp_type='double', default='-1.0', group='EF_SAFETY_INPUT'),
        Field(name='speed_mps', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='off_runway_steps', cpp_type='int', default='0', group='EF_SAFETY_INPUT'),
        Field(name='off_runway_terminate_speed', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='off_runway_terminate_grace_s', cpp_type='double', default='0.0', group='EF_SAFETY_INPUT'),
        Field(name='time_step_s', cpp_type='double', default='0.05', group='EF_SAFETY_INPUT'),
        Field(name='off_runway_terminate_penalty', cpp_type='double', default='-200.0', group='EF_SAFETY_INPUT'),
    ),
    file_footer=FILE_FOOTER,
)
