// X-macro list of TrainingProjectionEvent fields.
//
// Consumers define EF_TRAINING_PROJECTION_EVENT_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_TRAINING_PROJECTION_EVENT_FIELD(LethalityChainHeader, header, {})
EF_TRAINING_PROJECTION_EVENT_FIELD(std::vector<std::uint64_t>, consumed_event_ids, {})
EF_TRAINING_PROJECTION_EVENT_FIELD(std::string, consumer_node_id, {})
EF_TRAINING_PROJECTION_EVENT_FIELD(std::string, consumer_version, {})
EF_TRAINING_PROJECTION_EVENT_FIELD(std::string, projection_kind, "training_consumer")
EF_TRAINING_PROJECTION_EVENT_FIELD(std::string, reward_term, {})
EF_TRAINING_PROJECTION_EVENT_FIELD(double, reward_delta, 0.0)
EF_TRAINING_PROJECTION_EVENT_FIELD(std::string, terminal_reason, {})
EF_TRAINING_PROJECTION_EVENT_FIELD(bool, fact_source, false)

#undef EF_TRAINING_PROJECTION_EVENT_FIELD
