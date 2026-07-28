// X-macro list of PilotReportMaintainedBatchContract fields.
//
// Consumers define EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD(
// type, name, default_value) before including this file; the macro is
// #undef'd here after expansion.
//
// NOTE(I35): the trailing ground_static_status field has never been
// bound to Python (pre-existing binding-surface omission). I35
// preserves that omission as-is instead of newly exposing the field;
// see bindings_runtime.cpp for the held hand-written binding.

EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD(shared_core_type, shared_core, {})
EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD(air_owner_slice_type, air, {})
EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD(naval_command_authority_type, naval_command_authority, {})
EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD(ground_static_status_type, ground_static_status, {})

#undef EF_PILOT_REPORT_MAINTAINED_BATCH_CONTRACT_FIELD
