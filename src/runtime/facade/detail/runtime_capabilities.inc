// X-macro list of RuntimeCapabilities fields.
//
// Consumers define EF_RUNTIME_CAPABILITIES_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_batch_runtime, false)
EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_compiled_episode_controller, false)
EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_compiled_execution_step, false)
EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_gpu_visual, false)
EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_gpu_observation, false)
EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_gpu_flight_shaping, false)
EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_device_observation_view, false)
EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_resident_state, false)
EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_exact_gpu_backend, false)
EF_RUNTIME_CAPABILITIES_FIELD(bool, supports_shadow_compare, false)
EF_RUNTIME_CAPABILITIES_FIELD(std::string, maintained_baseline_backend_profile_id, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, maintained_baseline_parity_budget_ref, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, maintained_baseline_profile_status, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, device_observation_view_candidate_profile_id, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, device_observation_view_rejection_reason, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, exact_gpu_backend_candidate_profile_id, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, exact_gpu_backend_rejection_reason, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, resident_state_candidate_profile_id, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, resident_state_candidate_parity_budget_ref, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, resident_state_rejection_reason, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, shadow_compare_candidate_profile_id, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, shadow_compare_candidate_parity_budget_ref, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, shadow_compare_rejection_reason, {})
EF_RUNTIME_CAPABILITIES_FIELD(std::string, multi_fidelity_rejection_reason, {})

#undef EF_RUNTIME_CAPABILITIES_FIELD
