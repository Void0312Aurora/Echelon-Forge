// X-macro list of ObservationBatchRequest fields.
//
// Consumers define EF_OBSERVATION_BATCH_REQUEST_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_OBSERVATION_BATCH_REQUEST_FIELD(std::vector<WorldEntityRef>, refs, {})
EF_OBSERVATION_BATCH_REQUEST_FIELD(bool, include_agent_observations, true)
EF_OBSERVATION_BATCH_REQUEST_FIELD(bool, include_instrument_states, false)

#undef EF_OBSERVATION_BATCH_REQUEST_FIELD
