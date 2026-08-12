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

void bind_runtime_batch_packet(nb::module_ &m) {
    nb::class_<ObservationBatchPacket> observation_batch_packet_class(m, "ObservationBatchPacket");
    observation_batch_packet_class.def(nb::init<>());
#define EF_OBSERVATION_BATCH_PACKET_FIELD(type, name, default_value)                               \
    observation_batch_packet_class.def_rw(#name, &ObservationBatchPacket::name);
#include "runtime/facade/detail/batch/observation_batch_packet.inc"

    nb::class_<TaskingBatchPacket> tasking_batch_packet_class(m, "TaskingBatchPacket");
    tasking_batch_packet_class.def(nb::init<>());
#define EF_TASKING_BATCH_PACKET_FIELD(type, name, default_value)                                   \
    tasking_batch_packet_class.def_rw(#name, &TaskingBatchPacket::name);
#include "runtime/facade/detail/batch/tasking_batch_packet.inc"

    nb::class_<EngagementEventPacket> engagement_event_packet_class(m, "EngagementEventPacket");
    engagement_event_packet_class.def(nb::init<>());
#define EF_ENGAGEMENT_EVENT_PACKET_FIELD(type, name, default_value)                                \
    engagement_event_packet_class.def_rw(#name, &EngagementEventPacket::name);
#include "runtime/facade/detail/batch/engagement_event_packet.inc"

    nb::class_<ExecutionBatchStepResult>(m, "ExecutionBatchStepResult")
        .def(nb::init<>())
        .def_rw("step_results", &ExecutionBatchStepResult::step_results)
        .def_rw("execution_episode_states", &ExecutionBatchStepResult::execution_episode_states)
        .def_rw("rewards", &ExecutionBatchStepResult::rewards)
        .def_rw("terminated", &ExecutionBatchStepResult::terminated)
        .def_rw("truncated", &ExecutionBatchStepResult::truncated)
        .def_rw("status_vectors", &ExecutionBatchStepResult::status_vectors)
        .def_rw("termination_reasons", &ExecutionBatchStepResult::termination_reasons)
        .def_rw("termination_specs", &ExecutionBatchStepResult::termination_specs)
        .def_rw("reward_breakdown_jsons", &ExecutionBatchStepResult::reward_breakdown_jsons)
        .def_rw("reward_reports", &ExecutionBatchStepResult::reward_reports)
        .def_rw("step_infos", &ExecutionBatchStepResult::step_infos)
        .def_rw("step_info_valid_flags", &ExecutionBatchStepResult::step_info_valid_flags)
        .def_rw("controller_state_changed_flags",
                &ExecutionBatchStepResult::controller_state_changed_flags)
        .def_rw("observation_packet", &ExecutionBatchStepResult::observation_packet)
        .def_rw("tasking_packet", &ExecutionBatchStepResult::tasking_packet);
}
