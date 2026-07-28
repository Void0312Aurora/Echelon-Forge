"""Declarative DTO schema for KillChainRuntimeFacade fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of KillChainRuntimeFacade fields.\n'
    '//\n'
    '// Consumers define EF_KILL_CHAIN_RUNTIME_FACADE_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_KILL_CHAIN_RUNTIME_FACADE_FIELD\n'
)


SCHEMA = DtoSchema(
    name='kill_chain_runtime_facade',
    output_path='src/runtime/contracts/detail/kill_chain_runtime_facade.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='schema_version', cpp_type='std::uint32_t', default='1', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='schema_name', cpp_type='std::string', default='"a2.kill_chain_runtime_facade.v1"', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='runtime_dto_authority', cpp_type='bool', default='true', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='runtime_parameter_retuning', cpp_type='bool', default='false', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='calibration_authority', cpp_type='bool', default='false', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='real_world_pk', cpp_type='bool', default='false', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='approach_fact', cpp_type='KillChainApproachFact', default='{}', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='fuze_decision', cpp_type='KillChainFuzeDecision', default='{}', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='warhead_load_field', cpp_type='KillChainWarheadLoadField', default='{}', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='target_susceptibility', cpp_type='KillChainTargetSusceptibility', default='{}', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='component_responses', cpp_type='std::vector<KillChainComponentResponseFact>', default='{}', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
        Field(name='consequence_projection', cpp_type='KillChainConsequenceProjection', default='{}', group='EF_KILL_CHAIN_RUNTIME_FACADE_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
