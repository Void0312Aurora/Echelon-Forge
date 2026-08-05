"""Declarative DTO schema for RuntimeCounterfactualSnapshot fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of RuntimeCounterfactualSnapshot fields.\n'
    '//\n'
    '// Consumers define EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(type, name,\n'
    '// default_value) before including this file; the macro is #undef\'d here\n'
    '// after expansion.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='runtime_counterfactual_snapshot',
    output_path='src/runtime/facade/detail/runtime/runtime_counterfactual_snapshot.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='worldline_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='parent_worldline_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='deterministic_seed', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='world_index', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='entity_id', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='x', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='y', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='z', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='vx', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='vy', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='vz', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='heading', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='pitch', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='roll', cpp_type='double', default='0.0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='snapshot_version', cpp_type='std::uint64_t', default='0', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='barrier_id', cpp_type='std::string', default='"counterfactual_selected_slice"', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='fidelity_profile_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='provider_family', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='selected_stage_node_id', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='cadence_reason', cpp_type='std::string', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
        Field(name='evidence_refs', cpp_type='std::vector<std::string>', default='{}', group='EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
