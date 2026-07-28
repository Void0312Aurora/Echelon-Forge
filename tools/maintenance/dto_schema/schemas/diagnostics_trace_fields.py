"""Declarative DTO schema for DiagnosticsTrace fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of DiagnosticsTrace fields.\n'
    '//\n'
    '// Consumers define EF_DIAGNOSTICS_TRACE_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_DIAGNOSTICS_TRACE_FIELD\n'
)


SCHEMA = DtoSchema(
    name='diagnostics_trace',
    output_path='src/runtime/contracts/detail/diagnostics_trace.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='trace_id', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='parent_trace_id', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='chain_id', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='track_id', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='launch_request_id', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='launch_event_id', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='munition', cpp_type='EngagementEntityRef', default='{}', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='effects_event_id', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='damage_report_id', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='observation_packet_version', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='source_snapshot_version', cpp_type='std::uint64_t', default='0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='barrier_id', cpp_type='std::string', default='"export"', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='barrier_detail', cpp_type='std::string', default='"maintained_facade_export"', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='source_time_s', cpp_type='double', default='0.0', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='source_node_id', cpp_type='std::string', default='{}', group='EF_DIAGNOSTICS_TRACE_FIELD'),
        Field(name='export_node_id', cpp_type='std::string', default='{}', group='EF_DIAGNOSTICS_TRACE_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
