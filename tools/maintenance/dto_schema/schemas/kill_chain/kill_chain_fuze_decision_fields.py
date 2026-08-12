"""Declarative DTO schema for KillChainFuzeDecision fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of KillChainFuzeDecision fields.\n'
    '//\n'
    '// Consumers define EF_KILL_CHAIN_FUZE_DECISION_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_KILL_CHAIN_FUZE_DECISION_FIELD\n'
)


SCHEMA = DtoSchema(
    name='kill_chain_fuze_decision',
    output_path='src/runtime/contracts/detail/kill_chain/kill_chain_fuze_decision.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='owner_stage', cpp_type='std::string', default='"fuze_decision"', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='fuze_type', cpp_type='std::string', default='"unknown"', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='detonated', cpp_type='bool', default='false', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='outcome_state', cpp_type='std::string', default='"unknown"', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='detonation_time_s', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='detonation_probability', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='fuze_quality', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='sensor_opportunity_score', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='terminal_track_valid', cpp_type='bool', default='false', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='target_detected', cpp_type='bool', default='false', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='target_detection_confidence', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='target_detection_threshold', cpp_type='double', default='0.0', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
        Field(name='detonation_point_source', cpp_type='std::string', default='"unknown"', group='EF_KILL_CHAIN_FUZE_DECISION_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
