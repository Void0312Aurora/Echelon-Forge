// X-macro list of LeaderIntentMaintainedBatchContract fields.
//
// Consumers define EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(
// type, name, default_value) before including this file; the macro is
// #undef'd here after expansion.
//
// NOTE(I35): the trailing ground_static_status field has never been
// bound to Python (pre-existing binding-surface omission). I35
// preserves that omission as-is instead of newly exposing the field;
// see bindings_runtime.cpp for the held hand-written binding.

EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(shared_core_type, shared_core, {})
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(LeaderPhase, phase_id, LeaderPhase::Idle)
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(int, element_phase_id, 0)
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(air_recovery_type, air_recovery, {})
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(FormationMode, formation_mode_id, FormationMode::Unspecified)
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(bool, join_required_flag, false)
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(bool, rejoin_required_flag, false)
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(air_takeoff_type, air_takeoff, {})
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(air_formation_type, air_formation, {})
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(naval_command_authority_type, naval_command_authority, {})
EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD(ground_static_status_type, ground_static_status, {})

#undef EF_LEADER_INTENT_MAINTAINED_BATCH_CONTRACT_FIELD
