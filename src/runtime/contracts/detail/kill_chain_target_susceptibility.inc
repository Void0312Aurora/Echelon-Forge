// X-macro list of KillChainTargetSusceptibility fields.
//
// Consumers define EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(type,
// name, default_value) before including this file; the macro is
// #undef'd here after expansion.

EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(std::string, owner_stage, "target_susceptibility")
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(bool, vulnerability_profile_present, false)
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(bool, vulnerability_profile_synthetic, true)
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(bool, calibrated_evidence, false)
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(bool, pk_authority, false)
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(bool, deterministic_fuze_authority, false)
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(std::string, calibration_status, "none")
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(std::string, aspect_bucket, "unknown")
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(double, family_scale, 1.0)
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(double, aspect_scale, 1.0)
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(double, closure_scale, 1.0)
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(double, miss_distance_scale, 1.0)
EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD(double, effect_scale, 1.0)

#undef EF_KILL_CHAIN_TARGET_SUSCEPTIBILITY_FIELD
