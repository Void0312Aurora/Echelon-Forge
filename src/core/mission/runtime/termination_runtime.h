#pragma once

#include <string>

enum class TerminationReasonCode {
    Running = 0,
    NanGuard,
    CrashHealth,
    FailfastDeepStall,
    FailfastInvertedLowAlt,
    FailfastExtremePitch,
    GearCollapse,
    OffRunwayTerminate,
    SuccessWaypoint,
    SuccessObjective,
    Success,
    FailureUnknown,
    TerminatedUnknown,
    Timeout,
};

struct SafetyRuntimeInputs {
#define EF_SAFETY_INPUT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/safety_runtime_inputs.inc"
};

struct SafetyRuntimeProducts {
#define EF_SAFETY_PRODUCT(type, name, default_value) type name = default_value;
#include "core/mission/runtime/detail/safety_runtime_products.inc"
};

SafetyRuntimeProducts compute_safety_runtime(const SafetyRuntimeInputs &inputs);
TerminationReasonCode finalize_termination_reason(TerminationReasonCode current_reason,
                                                  bool terminated, bool truncated,
                                                  double status_flag);
std::string termination_reason_name(TerminationReasonCode reason);
