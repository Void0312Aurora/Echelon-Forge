"""Declarative DTO schema for RuntimeCounterfactualBranchRequest fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeCounterfactualBranchRequest fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_counterfactual_branch_request',
    output_path='src/runtime/facade/detail/runtime_counterfactual_branch_request.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='baseline_setup', cpp_type='BatchWorldSetupRequest', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='entity_ref', cpp_type='WorldEntityRef', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='fidelity_request', cpp_type='RuntimeFidelityRequest', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='deterministic_seed', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='replay_envelope_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='branch_point_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='branch_worldline_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='parent_worldline_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='restore_barrier_id', cpp_type='std::string', default='"counterfactual_selected_slice"', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='cadence_reason', cpp_type='std::string', default='"selected_slice_cadence_trace_runtime_window"', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='mutation_dx', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='mutation_dy', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='mutation_dz', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='mutation_dvx', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='mutation_dvy', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='mutation_dvz', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='mutation_dheading', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='allow_raw_authoritative_state_mutation', cpp_type='bool', default='false', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
