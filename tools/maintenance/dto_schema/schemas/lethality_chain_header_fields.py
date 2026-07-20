"""Declarative DTO schema for LethalityChainHeader fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of LethalityChainHeader fields.\n'
    '//\n'
    '// Consumers define EF_LETHALITY_CHAIN_HEADER_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_LETHALITY_CHAIN_HEADER_FIELD\n'
)


SCHEMA = DtoSchema(
    name='lethality_chain_header',
    output_path='src/runtime/contracts/detail/lethality_chain_header.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='schema_version', cpp_type='std::uint32_t', default='kLethalityChainContractSchemaVersion', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='chain_id', cpp_type='std::uint64_t', default='0', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='event_id', cpp_type='std::uint64_t', default='0', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='parent_event_id', cpp_type='std::uint64_t', default='0', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='stage', cpp_type='std::string', default='"unknown"', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='status', cpp_type='std::string', default='"not_evaluated"', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='reason', cpp_type='std::string', default='{}', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='source_frame', cpp_type='std::uint64_t', default='0', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='munition', cpp_type='EngagementEntityRef', default='{}', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='shooter', cpp_type='EngagementEntityRef', default='{}', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='target', cpp_type='EngagementEntityRef', default='{}', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='producer_node_id', cpp_type='std::string', default='{}', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='fidelity_mode', cpp_type='std::string', default='"unspecified"', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='evidence_level', cpp_type='std::string', default='"uncalibrated"', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='observation_mode', cpp_type='std::string', default='std::string(kLethalityObservationModeSampledRuntime)', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='consumer_visibility', cpp_type='std::string', default='std::string(kLethalityConsumerVisibilityDiagnosticsAndTraining)', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
        Field(name='confidence', cpp_type='double', default='0.0', group='EF_LETHALITY_CHAIN_HEADER_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
