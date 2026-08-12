#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_experiment(nb::module_ &m) {
    nb::class_<RuntimeWorldLayoutRequest> runtime_world_layout_request_class(
        m, "RuntimeWorldLayoutRequest");
    runtime_world_layout_request_class.def(nb::init<>());
#define EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(type, name, default_value)                           \
    runtime_world_layout_request_class.def_rw(#name, &RuntimeWorldLayoutRequest::name);
#include "runtime/facade/detail/runtime/runtime_world_layout_request.inc"

    nb::class_<RuntimeWorldLayoutResult> runtime_world_layout_result_class(
        m, "RuntimeWorldLayoutResult");
    runtime_world_layout_result_class.def(nb::init<>());
#define EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(type, name, default_value)                            \
    runtime_world_layout_result_class.def_rw(#name, &RuntimeWorldLayoutResult::name);
#include "runtime/facade/detail/runtime/runtime_world_layout_result.inc"

    nb::class_<RuntimeCounterfactualBranchRequest> runtime_counterfactual_branch_request_class(
        m, "RuntimeCounterfactualBranchRequest");
    runtime_counterfactual_branch_request_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(type, name, default_value)                  \
    runtime_counterfactual_branch_request_class.def_rw(#name,                                      \
                                                       &RuntimeCounterfactualBranchRequest::name);
#include "runtime/facade/detail/runtime/runtime_counterfactual_branch_request.inc"

    nb::class_<RuntimeCounterfactualRestoreRequest> runtime_counterfactual_restore_request_class(
        m, "RuntimeCounterfactualRestoreRequest");
    runtime_counterfactual_restore_request_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(type, name, default_value)                 \
    runtime_counterfactual_restore_request_class.def_rw(                                           \
        #name, &RuntimeCounterfactualRestoreRequest::name);
#include "runtime/facade/detail/runtime/runtime_counterfactual_restore_request.inc"

    nb::class_<RuntimeCounterfactualRestoreResult> runtime_counterfactual_restore_result_class(
        m, "RuntimeCounterfactualRestoreResult");
    runtime_counterfactual_restore_result_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(type, name, default_value)                  \
    runtime_counterfactual_restore_result_class.def_rw(#name,                                      \
                                                       &RuntimeCounterfactualRestoreResult::name);
#include "runtime/facade/detail/runtime/runtime_counterfactual_restore_result.inc"

    nb::class_<RuntimeCounterfactualBranchResult> runtime_counterfactual_branch_result_class(
        m, "RuntimeCounterfactualBranchResult");
    runtime_counterfactual_branch_result_class.def(nb::init<>());
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(type, name, default_value)                   \
    runtime_counterfactual_branch_result_class.def_rw(#name,                                       \
                                                      &RuntimeCounterfactualBranchResult::name);
#include "runtime/facade/detail/runtime/runtime_counterfactual_branch_result.inc"

    nb::class_<RuntimeExperimentStepRequest> runtime_experiment_step_request_class(
        m, "RuntimeExperimentStepRequest");
    runtime_experiment_step_request_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(type, name, default_value)                        \
    runtime_experiment_step_request_class.def_rw(#name, &RuntimeExperimentStepRequest::name);
#include "runtime/facade/detail/runtime/runtime_experiment_step_request.inc"

    nb::class_<RuntimeExperimentRequest> runtime_experiment_request_class(
        m, "RuntimeExperimentRequest");
    runtime_experiment_request_class.def(nb::init<>());
#define EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(type, name, default_value)                             \
    runtime_experiment_request_class.def_rw(#name, &RuntimeExperimentRequest::name);
#include "runtime/facade/detail/runtime/runtime_experiment_request.inc"
}
