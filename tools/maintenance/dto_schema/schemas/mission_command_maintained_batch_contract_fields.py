"""Declarative DTO schema for MissionCommandMaintainedBatchContract fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of MissionCommandMaintainedBatchContract fields.\n'
    '//\n'
    '// Consumers define EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(\n'
    '// type, name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '//\n'
    '// NOTE(I35): the trailing ground_static_task field has never been\n'
    '// bound to Python (pre-existing binding-surface omission). I35\n'
    '// preserves that omission as-is instead of newly exposing the field;\n'
    '// see bindings_runtime.cpp for the held hand-written binding.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='mission_command_maintained_batch_contract',
    output_path='src/runtime/contracts/detail/mission_command_maintained_batch_contract.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='shared_core', cpp_type='shared_core_type', default='{}', group='EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_recovery', cpp_type='air_recovery_type', default='{}', group='EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_takeoff', cpp_type='air_takeoff_type', default='{}', group='EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_formation', cpp_type='air_formation_type', default='{}', group='EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='naval_stationing', cpp_type='naval_stationing_type', default='{}', group='EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='naval_embarked_helo', cpp_type='naval_embarked_helo_type', default='{}', group='EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='ground_static_task', cpp_type='ground_static_task_type', default='{}', group='EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD', hidden=True),
    ),
    file_footer=FILE_FOOTER,
)
