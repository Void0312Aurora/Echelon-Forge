"""Declarative DTO schema for ConditionalObjectiveProducts fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of ConditionalObjectiveProducts fields.\n'
    '//\n'
    '// Consumers define EF_OBJECTIVE_PRODUCT(type, name, default_value) before\n'
    "// including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_OBJECTIVE_PRODUCT\n'
)


SCHEMA = DtoSchema(
    name='objective_products',
    output_path='src/core/mission/runtime/detail/objective_products.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='valid', cpp_type='bool', default='false', group='EF_OBJECTIVE_PRODUCT', readonly=True),
        Field(name='matched', cpp_type='bool', default='false', group='EF_OBJECTIVE_PRODUCT', readonly=True),
        Field(name='unknown_property', cpp_type='bool', default='false', group='EF_OBJECTIVE_PRODUCT', readonly=True),
        Field(name='status0', cpp_type='double', default='0.0', group='EF_OBJECTIVE_PRODUCT', readonly=True),
        Field(name='status1', cpp_type='double', default='0.0', group='EF_OBJECTIVE_PRODUCT', readonly=True),
        Field(name='status2', cpp_type='double', default='0.0', group='EF_OBJECTIVE_PRODUCT', readonly=True),
        Field(name='status_count', cpp_type='int', default='0', group='EF_OBJECTIVE_PRODUCT', readonly=True),
        Field(name='success_runway_cross_penalty', cpp_type='double', default='0.0', group='EF_OBJECTIVE_PRODUCT', readonly=True),
        Field(name='success_ground_track_error_penalty', cpp_type='double', default='0.0', group='EF_OBJECTIVE_PRODUCT', readonly=True),
        Field(name='objective_bonus', cpp_type='double', default='0.0', group='EF_OBJECTIVE_PRODUCT', readonly=True),
    ),
    file_footer=FILE_FOOTER,
)
