"""Declarative DTO schema for ApproachRewardInputs fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ApproachRewardInputs fields.\n'
    '//\n'
    '// Consumers define EF_APPROACH_INPUT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_APPROACH_INPUT\n'
)


SCHEMA = DtoSchema(
    name='approach_reward_inputs',
    output_path='src/core/mission/runtime/detail/approach_reward_inputs.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='valid', cpp_type='bool', default='false', group='EF_APPROACH_INPUT'),
        Field(name='ils_valid', cpp_type='bool', default='false', group='EF_APPROACH_INPUT'),
        Field(name='ils_loc_dev', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='ils_gs_dev', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='ils_dme_m', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='has_prev_loc', cpp_type='bool', default='false', group='EF_APPROACH_INPUT'),
        Field(name='prev_loc_abs', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='has_prev_gs', cpp_type='bool', default='false', group='EF_APPROACH_INPUT'),
        Field(name='prev_gs_abs', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='has_prev_dme', cpp_type='bool', default='false', group='EF_APPROACH_INPUT'),
        Field(name='prev_dme_m', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='localizer_weight', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='localizer_deadband', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='localizer_norm', cpp_type='double', default='1.0', group='EF_APPROACH_INPUT'),
        Field(name='localizer_power', cpp_type='double', default='2.0', group='EF_APPROACH_INPUT'),
        Field(name='localizer_clip', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='localizer_improve_weight', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='glideslope_weight', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='glideslope_deadband', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='glideslope_norm', cpp_type='double', default='1.0', group='EF_APPROACH_INPUT'),
        Field(name='glideslope_power', cpp_type='double', default='2.0', group='EF_APPROACH_INPUT'),
        Field(name='glideslope_clip', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='glideslope_improve_weight', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='dme_progress_weight', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='dme_progress_localizer_band', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='dme_progress_glideslope_band', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='dme_progress_quality_power', cpp_type='double', default='1.0', group='EF_APPROACH_INPUT'),
        Field(name='capture_bonus', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='capture_localizer_band', cpp_type='double', default='0.20', group='EF_APPROACH_INPUT'),
        Field(name='capture_glideslope_band', cpp_type='double', default='0.20', group='EF_APPROACH_INPUT'),
        Field(name='sink_rate_weight', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='flare_agl_m', cpp_type='double', default='20.0', group='EF_APPROACH_INPUT'),
        Field(name='curr_alt_agl_m', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='sink_rate_mps', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='sink_rate_deadband_mps', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
        Field(name='sink_rate_norm_mps', cpp_type='double', default='2.0', group='EF_APPROACH_INPUT'),
        Field(name='sink_rate_power', cpp_type='double', default='2.0', group='EF_APPROACH_INPUT'),
        Field(name='sink_rate_clip', cpp_type='double', default='0.0', group='EF_APPROACH_INPUT'),
    ),
    file_footer=FILE_FOOTER,
)
