// X-macro list of ExecutionBatchStepRequest fields.
//
// Consumers define EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(std::vector<WorldExecutionEpisodeStepRequest>, step_requests, {})
EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(bool, include_agent_observations, true)
EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(bool, include_instrument_states, false)

#undef EF_EXECUTION_BATCH_STEP_REQUEST_FIELD
