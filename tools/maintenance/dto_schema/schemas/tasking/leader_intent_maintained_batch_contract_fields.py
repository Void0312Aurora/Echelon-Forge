"""Declarative DTO schema for LeaderIntentMaintainedBatchContract fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of LeaderIntentMaintainedBatchContract fields.\n'
    '//\n'
    '// Consumers define EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(\n'
    '// type, name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '//\n'
    '// NOTE(I35): the trailing ground_static_status field has never been\n'
    '// bound to Python (pre-existing binding-surface omission). I35\n'
    '// preserves that omission as-is instead of newly exposing the field;\n'
    '// see bindings_runtime.cpp for the held hand-written binding.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='leader_intent_maintained_batch_contract',
    output_path='src/runtime/contracts/detail/tasking/leader_intent_maintained_batch_contract.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='shared_core', cpp_type='shared_core_type', default='{}', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='phase_id', cpp_type='LeaderPhase', default='LeaderPhase::Idle', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='element_phase_id', cpp_type='int', default='0', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_recovery', cpp_type='air_recovery_type', default='{}', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='formation_mode_id', cpp_type='FormationMode', default='FormationMode::Unspecified', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='join_required_flag', cpp_type='bool', default='false', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='rejoin_required_flag', cpp_type='bool', default='false', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_takeoff', cpp_type='air_takeoff_type', default='{}', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_formation', cpp_type='air_formation_type', default='{}', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='naval_command_authority', cpp_type='naval_command_authority_type', default='{}', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='ground_static_status', cpp_type='ground_static_status_type', default='{}', group='EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD', hidden=True),
    ),
    file_footer=FILE_FOOTER,
)
