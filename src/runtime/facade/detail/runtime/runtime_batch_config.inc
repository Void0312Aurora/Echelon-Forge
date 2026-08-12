// X-macro list of RuntimeBatchConfig fields.
//
// Consumers define EF_RUNTIME_BATCH_CONFIG_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_RUNTIME_BATCH_CONFIG_FIELD(std::size_t, world_count, 0)
EF_RUNTIME_BATCH_CONFIG_FIELD(std::size_t, worker_threads, 1)

#undef EF_RUNTIME_BATCH_CONFIG_FIELD
