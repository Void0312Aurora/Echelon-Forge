"""Declarative DTO schema for ApproachRewardProducts fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ApproachRewardProducts fields.\n'
    '//\n'
    '// Consumers define EF_APPROACH_PRODUCT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_APPROACH_PRODUCT\n'
)


SCHEMA = DtoSchema(
    name='approach_reward_products',
    output_path='src/core/mission/runtime/detail/approach_reward_products.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='valid', cpp_type='bool', default='false', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='approach_localizer', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='approach_localizer_improve', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='approach_glideslope', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='approach_glideslope_improve', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='approach_dme_progress', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='approach_capture_bonus', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='landing_sink_rate_penalty', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='clear_history', cpp_type='bool', default='false', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='next_prev_valid', cpp_type='bool', default='false', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='next_prev_loc_abs', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='next_prev_gs_abs', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
        Field(name='next_prev_dme_m', cpp_type='double', default='0.0', group='EF_APPROACH_PRODUCT', readonly=True),
    ),
    file_footer=FILE_FOOTER,
)
