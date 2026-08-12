"""Declarative DTO schema for RuntimeCounterfactualBranchResult fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeCounterfactualBranchResult fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_counterfactual_branch_result',
    output_path='src/runtime/facade/detail/runtime/runtime_counterfactual_branch_result.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='admitted', cpp_type='bool', default='false', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD'),
        Field(name='rejection_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD'),
        Field(name='fidelity_admission', cpp_type='RuntimeFidelityAdmission', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD'),
        Field(name='parent_snapshot', cpp_type='RuntimeCounterfactualSnapshot', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD'),
        Field(name='branch_snapshot', cpp_type='RuntimeCounterfactualSnapshot', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD'),
        Field(name='comparison', cpp_type='RuntimeWorldlineComparison', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD'),
        Field(name='restore_result', cpp_type='RuntimeCounterfactualRestoreResult', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
