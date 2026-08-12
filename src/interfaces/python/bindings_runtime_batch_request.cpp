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

void bind_runtime_batch_request(nb::module_ &m) {
    nb::class_<ObservationBatchRequest> observation_batch_request_class(m,
                                                                        "ObservationBatchRequest");
    observation_batch_request_class.def(nb::init<>());
#define EF_OBSERVATION_BATCH_REQUEST_FIELD(type, name, default_value)                              \
    observation_batch_request_class.def_rw(#name, &ObservationBatchRequest::name);
#include "runtime/facade/detail/batch/observation_batch_request.inc"

    nb::class_<TaskingBatchRequest> tasking_batch_request_class(m, "TaskingBatchRequest");
    tasking_batch_request_class.def(nb::init<>());
#define EF_TASKING_BATCH_REQUEST_FIELD(type, name, default_value)                                  \
    tasking_batch_request_class.def_rw(#name, &TaskingBatchRequest::name);
#include "runtime/facade/detail/batch/tasking_batch_request.inc"

    nb::class_<EngagementBatchRequest> engagement_batch_request_class(m, "EngagementBatchRequest");
    engagement_batch_request_class.def(nb::init<>());
#define EF_ENGAGEMENT_BATCH_REQUEST_FIELD(type, name, default_value)                               \
    engagement_batch_request_class.def_rw(#name, &EngagementBatchRequest::name);
#include "runtime/facade/detail/batch/engagement_batch_request.inc"

    nb::class_<ExecutionBatchStepRequest> execution_batch_step_request_class(
        m, "ExecutionBatchStepRequest");
    execution_batch_step_request_class.def(nb::init<>());
#define EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(type, name, default_value)                           \
    execution_batch_step_request_class.def_rw(#name, &ExecutionBatchStepRequest::name);
#include "runtime/facade/detail/batch/execution_batch_step_request.inc"
}
