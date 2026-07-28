// X-macro list of TaskOrderAirFormationDirective fields.
//
// Consumers define EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(std::uint64_t, formation_template_id, 0)
EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(std::uint64_t, formation_contract_id, 0)
EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(FormationRole, formation_role_id, FormationRole::Unspecified)
EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(WingmanSlot, wingman_slot_id, WingmanSlot::Unspecified)
EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(int, join_policy_id, 0)
EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(int, rejoin_policy_id, 0)
EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(int, mutual_support_mode, 0)
EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD(std::uint64_t, support_sector_id, 0)

#undef EF_TASK_ORDER_AIR_FORMATION_DIRECTIVE_FIELD
