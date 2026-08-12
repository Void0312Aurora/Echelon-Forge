"""Declarative DTO schema for DamageReport fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of DamageReport fields.\n'
    '//\n'
    '// Consumers define EF_DAMAGE_REPORT_FIELD(type, name, default_value)\n'
    "// before including this file; the macro is #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_DAMAGE_REPORT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='damage_report',
    output_path='src/runtime/contracts/detail/damage/damage_report.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='report_id', cpp_type='std::uint64_t', default='0', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='target', cpp_type='EngagementEntityRef', default='{}', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='source_event_id', cpp_type='std::uint64_t', default='0', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='hp_delta', cpp_type='double', default='0.0', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='system_health_delta', cpp_type='double', default='0.0', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='platform_damage_state_delta', cpp_type='std::string', default='{}', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='mission_kill', cpp_type='bool', default='false', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='mobility_kill', cpp_type='bool', default='false', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='sensor_kill', cpp_type='bool', default='false', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='survivability_kill', cpp_type='bool', default='false', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='forced_landing', cpp_type='bool', default='false', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='flight_control_kill', cpp_type='bool', default='false', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='propulsion_kill', cpp_type='bool', default='false', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='crew_kill', cpp_type='bool', default='false', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='loss_state_from', cpp_type='std::string', default='"unknown"', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='loss_state_to', cpp_type='std::string', default='"unknown"', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='destroyed', cpp_type='bool', default='false', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='report_time_s', cpp_type='double', default='0.0', group='EF_DAMAGE_REPORT_FIELD'),
        Field(name='producer_node_id', cpp_type='std::string', default='{}', group='EF_DAMAGE_REPORT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
