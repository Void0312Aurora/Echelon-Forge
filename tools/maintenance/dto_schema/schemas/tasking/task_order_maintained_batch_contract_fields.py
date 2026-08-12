"""Declarative DTO schema for TaskOrderMaintainedBatchContract fields."""

from __future__ import annotations

from tools.maintenance.dto_schema.model import DtoSchema, Field


FILE_HEADER = (
    '// X-macro list of TaskOrderMaintainedBatchContract fields.\n'
    '//\n'
    '// Consumers define EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(type,\n'
    '// name, default_value) before including this file; the macro is\n'
    "// #undef'd here after expansion.\n"
    '//\n'
    '// NOTE(I35): the trailing ground_static_task field has never been\n'
    '// bound as a Python property (pre-existing binding-surface omission;\n'
    '// the slice stays reachable through the pre-existing\n'
    '// task_order_maintained_ground_static_task free function in\n'
    '// bindings_command.cpp). I35 preserves that omission as-is; see\n'
    '// bindings_runtime.cpp for the held hand-written binding.\n'
    '\n'
)
FILE_FOOTER = (
    '\n'
    '#undef EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD\n'
)


SCHEMA = DtoSchema(
    name='task_order_maintained_batch_contract',
    output_path='src/runtime/contracts/detail/tasking/task_order_maintained_batch_contract.inc',
    file_header=FILE_HEADER,
    fields=(
        Field(name='shared_core', cpp_type='shared_core_type', default='{}', group='EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_tasking_identity', cpp_type='air_tasking_identity_type', default='{}', group='EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_stationing', cpp_type='air_stationing_type', default='{}', group='EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_recovery', cpp_type='air_recovery_type', default='{}', group='EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_takeoff', cpp_type='air_takeoff_type', default='{}', group='EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='air_formation', cpp_type='air_formation_type', default='{}', group='EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='naval_command_authority', cpp_type='naval_command_authority_type', default='{}', group='EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='naval_stationing', cpp_type='naval_stationing_type', default='{}', group='EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD'),
        Field(name='ground_static_task', cpp_type='ground_static_task_type', default='{}', group='EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD', hidden=True),
    ),
    file_footer=FILE_FOOTER,
)
