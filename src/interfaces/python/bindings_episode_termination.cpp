#include "interfaces/python/bindings_episode_detail.h"

#include "core/geometry/spatial_query_runtime.h"
#include "core/mission/episode/episode_reward_breakdown.h"
#include "core/mission/episode/execution_episode_batch_prepare.h"
#include "core/mission/runtime/execution_episode_runtime.h"
#include "core/mission/episode/execution_episode_state.h"
#include "core/mission/runtime/execution_frame_runtime.h"
#include "core/mission/runtime/execution_observation_runtime.h"
#include "core/mission/runtime/execution_step_runtime.h"
#include "core/mission/runtime/mission_runtime.h"
#include "core/mission/runtime/objective_runtime.h"
#include "core/mission/runtime/reward_runtime.h"
#include "core/mission/runtime/termination_runtime.h"

void bind_episode_termination(nb::module_ &m) {
    nb::enum_<TerminationReasonCode>(m, "TerminationReasonCode")
        .value("Running", TerminationReasonCode::Running)
        .value("NanGuard", TerminationReasonCode::NanGuard)
        .value("CrashHealth", TerminationReasonCode::CrashHealth)
        .value("FailfastDeepStall", TerminationReasonCode::FailfastDeepStall)
        .value("FailfastInvertedLowAlt", TerminationReasonCode::FailfastInvertedLowAlt)
        .value("FailfastExtremePitch", TerminationReasonCode::FailfastExtremePitch)
        .value("GearCollapse", TerminationReasonCode::GearCollapse)
        .value("OffRunwayTerminate", TerminationReasonCode::OffRunwayTerminate)
        .value("SuccessWaypoint", TerminationReasonCode::SuccessWaypoint)
        .value("SuccessObjective", TerminationReasonCode::SuccessObjective)
        .value("Success", TerminationReasonCode::Success)
        .value("FailureUnknown", TerminationReasonCode::FailureUnknown)
        .value("TerminatedUnknown", TerminationReasonCode::TerminatedUnknown)
        .value("Timeout", TerminationReasonCode::Timeout)
        .export_values();

    nb::class_<SafetyRuntimeInputs> safety_inputs_class(m, "SafetyRuntimeInputs");
    safety_inputs_class.def(nb::init<>());
#define EF_SAFETY_INPUT(type, name, default_value)                                                 \
    safety_inputs_class.def_rw(#name, &SafetyRuntimeInputs::name);
#include "core/mission/runtime/detail/safety_runtime_inputs.inc"

    nb::class_<SafetyRuntimeProducts> safety_products_class(m, "SafetyRuntimeProducts");
    safety_products_class.def(nb::init<>());
#define EF_SAFETY_PRODUCT(type, name, default_value)                                               \
    safety_products_class.def_ro(#name, &SafetyRuntimeProducts::name);
#include "core/mission/runtime/detail/safety_runtime_products.inc"

    m.def("compute_safety_runtime", &compute_safety_runtime, nb::arg("inputs"));
    m.def("finalize_termination_reason", &finalize_termination_reason, nb::arg("current_reason"),
          nb::arg("terminated"), nb::arg("truncated"), nb::arg("status_flag"));
    m.def("termination_reason_name", &termination_reason_name, nb::arg("reason"));
}
