// X-macro list of WorldLeaderIntentMaintainedAssignment fields.
//
// Consumers define EF_WORLD_LEADER_INTENT_MAINTAINED_ASSIGNMENT_FIELD(
// type, name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_WORLD_LEADER_INTENT_MAINTAINED_ASSIGNMENT_FIELD(std::uint64_t, world_index, 0)
EF_WORLD_LEADER_INTENT_MAINTAINED_ASSIGNMENT_FIELD(std::uint64_t, entity_id, 0)
EF_WORLD_LEADER_INTENT_MAINTAINED_ASSIGNMENT_FIELD(contract_type, leader_intent, {})

#undef EF_WORLD_LEADER_INTENT_MAINTAINED_ASSIGNMENT_FIELD
