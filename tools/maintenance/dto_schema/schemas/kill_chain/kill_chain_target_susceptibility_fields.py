"""Declarative DTO schema for KillChainTargetSusceptibility fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of KillChainTargetSusceptibility fields.\n'
    '//\n'
    '// Consumers define EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD\n'
)


SCHEMA = DtoSchema(
    name='kill_chain_target_susceptibility',
    output_path='src/runtime/contracts/detail/kill_chain/kill_chain_target_susceptibility.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='owner_stage', cpp_type='std::string', default='"target_susceptibility"', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='vulnerability_profile_present', cpp_type='bool', default='false', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='vulnerability_profile_synthetic', cpp_type='bool', default='true', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='calibrated_evidence', cpp_type='bool', default='false', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='pk_authority', cpp_type='bool', default='false', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='deterministic_fuze_authority', cpp_type='bool', default='false', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='calibration_status', cpp_type='std::string', default='"none"', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='aspect_bucket', cpp_type='std::string', default='"unknown"', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='family_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='aspect_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='closure_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='miss_distance_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
        Field(name='effect_scale', cpp_type='double', default='1.0', group='EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
