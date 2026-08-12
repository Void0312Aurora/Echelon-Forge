// X-macro list of TaskingBatchRequest fields.
//
// Consumers define EF_TASKING_BATCH_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_TASKING_BATCH_REQUEST_FIELD(std::vector<WorldEntityRef>, refs, {})
EF_TASKING_BATCH_REQUEST_FIELD(bool, include_mission_command_contracts, false)
EF_TASKING_BATCH_REQUEST_FIELD(bool, include_task_order_contracts, false)
EF_TASKING_BATCH_REQUEST_FIELD(bool, include_leader_intent_contracts, false)
EF_TASKING_BATCH_REQUEST_FIELD(bool, include_pilot_report_contracts, false)

#undef EF_TASKING_BATCH_REQUEST_FIELD
