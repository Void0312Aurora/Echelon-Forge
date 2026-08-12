"""Declarative DTO schema for RuntimeWorldlineComparison fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeWorldlineComparison fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_WORLDLINE_COMPARISON_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_worldline_comparison',
    output_path='src/runtime/facade/detail/runtime/runtime_worldline_comparison.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='comparable', cpp_type='bool', default='false', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='comparison_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='parent_worldline_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='branch_worldline_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='barrier_id', cpp_type='std::string', default='"counterfactual_selected_slice"', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='dx', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='dy', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='dz', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='dvx', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='dvy', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='dvz', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='dheading', cpp_type='double', default='0.0', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_WORLDLINE_COMPARISON_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
