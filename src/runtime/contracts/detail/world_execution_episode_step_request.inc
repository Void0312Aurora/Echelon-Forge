// X-macro list of WorldExecutionEpisodeStepRequest fields.
//
// Consumers define EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD(std::uint64_t, world_index, 0)
EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD(std::uint64_t, entity_id, 0)
EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD(StepEvaluationBatchConfig, config, {})
EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD(StepEvaluationBatchEnvState, env_state, {})

#undef EF_WORLD_EXECUTION_EPISODE_STEP_REQUEST_FIELD
