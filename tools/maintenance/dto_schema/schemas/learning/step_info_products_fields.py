"""Declarative DTO schema for StepInfoProducts fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of StepInfoProducts fields.\n'
    '//\n'
    '// Consumers define EF_STEP_INFO_PRODUCT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_STEP_INFO_PRODUCT\n'
)


SCHEMA = DtoSchema(
    name='step_info_products',
    output_path='src/core/mission/runtime/detail/step_info_products.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='valid', cpp_type='bool', default='false', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='on_runway', cpp_type='bool', default='true', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='gear_collapsed', cpp_type='bool', default='false', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='gear_stress', cpp_type='double', default='0.0', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='on_ground', cpp_type='bool', default='false', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='airborne', cpp_type='bool', default='false', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='preliftoff', cpp_type='bool', default='true', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='has_runway_frame', cpp_type='bool', default='false', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='on_runway_geom', cpp_type='bool', default='false', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='runway_cross_m', cpp_type='double', default='0.0', group='EF_STEP_INFO_PRODUCT', readonly=True),
        Field(name='runway_along_m', cpp_type='double', default='0.0', group='EF_STEP_INFO_PRODUCT', readonly=True),
    ),
    file_footer=FILE_FOOTER,
)
