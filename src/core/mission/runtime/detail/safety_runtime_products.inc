// X-macro list of SafetyRuntimeProducts fields.
//
// Consumers define EF_SAFETY_PRODUCT(type, name, default_value) before
// including this file; the macro is #undef'd here after expansion.
// Expansion sites: struct definition (termination_runtime.h) and
// SafetyRuntimeProducts Python bindings (bindings_episode.cpp).
//
// Field order is load-bearing: it fixes the member layout of the struct.

EF_SAFETY_PRODUCT(bool, valid, false)
EF_SAFETY_PRODUCT(bool, early_return, false)
EF_SAFETY_PRODUCT(bool, terminated, false)
EF_SAFETY_PRODUCT(double, status_flag, 0.0)
EF_SAFETY_PRODUCT(TerminationReasonCode, reason_code, TerminationReasonCode::Running)
EF_SAFETY_PRODUCT(double, survival, 0.0)
EF_SAFETY_PRODUCT(double, crash_penalty, 0.0)
EF_SAFETY_PRODUCT(double, nan_guard_marker, 0.0)
EF_SAFETY_PRODUCT(double, stall_penalty, 0.0)
EF_SAFETY_PRODUCT(double, overload_penalty, 0.0)
EF_SAFETY_PRODUCT(double, failfast_penalty, 0.0)
EF_SAFETY_PRODUCT(double, gear_collapse_penalty, 0.0)
EF_SAFETY_PRODUCT(double, off_runway_penalty, 0.0)
EF_SAFETY_PRODUCT(double, gear_stress_penalty, 0.0)
EF_SAFETY_PRODUCT(double, off_runway_terminate_penalty, 0.0)

#undef EF_SAFETY_PRODUCT
