"""Declarative DTO schema for PlatformConsequenceEvent fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of PlatformConsequenceEvent fields.\n'
    '//\n'
    '// Consumers define EF_PLATFORM_CONSEQUENCE_EVENT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_PLATFORM_CONSEQUENCE_EVENT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='platform_consequence_event',
    output_path='src/runtime/contracts/detail/damage/platform_consequence_event.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='header', cpp_type='LethalityChainHeader', default='{}', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='mission_capability_before', cpp_type='double', default='1.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='mission_capability_after', cpp_type='double', default='1.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='mobility_capability_before', cpp_type='double', default='1.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='mobility_capability_after', cpp_type='double', default='1.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='sensor_capability_before', cpp_type='double', default='1.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='sensor_capability_after', cpp_type='double', default='1.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='survivability_capability_before', cpp_type='double', default='1.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='survivability_capability_after', cpp_type='double', default='1.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='mission_kill', cpp_type='bool', default='false', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='mobility_kill', cpp_type='bool', default='false', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='sensor_kill', cpp_type='bool', default='false', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='survivability_kill', cpp_type='bool', default='false', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='flight_control_kill', cpp_type='bool', default='false', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='propulsion_kill', cpp_type='bool', default='false', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='forced_landing', cpp_type='bool', default='false', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='crew_kill', cpp_type='bool', default='false', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='control_delta', cpp_type='double', default='0.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='engine_delta', cpp_type='double', default='0.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='fuel_leak_delta', cpp_type='double', default='0.0', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='fire_state', cpp_type='std::string', default='"unknown"', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='aircraft_damage_state_before', cpp_type='std::string', default='{}', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='aircraft_damage_state_after', cpp_type='std::string', default='{}', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='aircraft_damage_state_delta', cpp_type='std::string', default='{}', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='air_system_hit_flags', cpp_type='std::string', default='{}', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='air_system_spatial_scales', cpp_type='std::string', default='{}', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='vulnerability_scale_trace', cpp_type='std::string', default='{}', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='loss_state_from', cpp_type='std::string', default='"unknown"', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
        Field(name='loss_state_to', cpp_type='std::string', default='"unknown"', group='EF_PLATFORM_CONSEQUENCE_EVENT_FIELD'),
    ),
    file_footer=FILE_FOOTER,
)
