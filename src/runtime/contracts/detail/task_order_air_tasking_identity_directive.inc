// X-macro list of TaskOrderAirTaskingIdentityDirective fields.
//
// Consumers define EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD(
// type, name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD(TaskType, task_type, TaskType::Idle)
EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD(std::uint64_t, element_id, 0)
EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD(std::uint64_t, package_id, 0)
EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD(std::uint64_t, lead_aircraft_id, 0)

#undef EF_TASK_ORDER_AIR_TASKING_IDENTITY_DIRECTIVE_FIELD
