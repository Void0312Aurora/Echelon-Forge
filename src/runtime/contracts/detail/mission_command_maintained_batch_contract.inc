// X-macro list of MissionCommandMaintainedBatchContract fields.
//
// Consumers define EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(
// type, name, default_value) before including this file; the macro is
// #undef'd here after expansion.
//
// NOTE(I35): the trailing ground_static_task field has never been
// bound to Python (pre-existing binding-surface omission). I35
// preserves that omission as-is instead of newly exposing the field;
// see bindings_runtime.cpp for the held hand-written binding.

EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(shared_core_type, shared_core, {})
EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(air_recovery_type, air_recovery, {})
EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(air_takeoff_type, air_takeoff, {})
EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(air_formation_type, air_formation, {})
EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(naval_stationing_type, naval_stationing, {})
EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(naval_embarked_helo_type, naval_embarked_helo, {})
EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD(ground_static_task_type, ground_static_task, {})

#undef EF_MISSION_COMMAND_MAINTAINED_BATCH_CONTRACT_FIELD
