// X-macro list of TaskOrderMaintainedBatchContract fields.
//
// Consumers define EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.
//
// NOTE(I35): the trailing ground_static_task field has never been
// bound as a Python property (pre-existing binding-surface omission;
// the slice stays reachable through the pre-existing
// task_order_maintained_ground_static_task free function in
// bindings_command.cpp). I35 preserves that omission as-is; see
// bindings_runtime.cpp for the held hand-written binding.

EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(shared_core_type, shared_core, {})
EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(air_tasking_identity_type, air_tasking_identity, {})
EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(air_stationing_type, air_stationing, {})
EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(air_recovery_type, air_recovery, {})
EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(air_takeoff_type, air_takeoff, {})
EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(air_formation_type, air_formation, {})
EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(naval_command_authority_type, naval_command_authority, {})
EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(naval_stationing_type, naval_stationing, {})
EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD(ground_static_task_type, ground_static_task, {})

#undef EF_TASK_ORDER_MAINTAINED_BATCH_CONTRACT_FIELD
