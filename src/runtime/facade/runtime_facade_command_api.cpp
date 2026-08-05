#include "runtime/facade/runtime_facade_internal.h"

#include <vector>

void RuntimeFacade::set_pilot_actions_batch(
    const std::vector<WorldPilotActionAssignment> &assignments) {
    (void)runtime_->inject(runtime::backend::InputBatch{.pilot_actions = assignments});
}

std::vector<LaunchEvent>
RuntimeFacade::apply_launch_requests_batch(const std::vector<LaunchRequest> &requests) {
    return runtime_->inject(runtime::backend::InputBatch{.launch_requests = requests})
        .launch_events;
}

void RuntimeFacade::set_mission_commands_maintained_batch(
    const std::vector<WorldMissionCommandMaintainedAssignment> &assignments) {
    (void)runtime_->inject(runtime::backend::InputBatch{.mission_commands = assignments});
}

void RuntimeFacade::set_task_orders_maintained_batch(
    const std::vector<WorldTaskOrderMaintainedAssignment> &assignments) {
    (void)runtime_->inject(runtime::backend::InputBatch{.task_orders = assignments});
}

void RuntimeFacade::set_leader_intents_maintained_batch(
    const std::vector<WorldLeaderIntentMaintainedAssignment> &assignments) {
    (void)runtime_->inject(runtime::backend::InputBatch{.leader_intents = assignments});
}

void RuntimeFacade::set_pilot_reports_maintained_batch(
    const std::vector<WorldPilotReportMaintainedAssignment> &assignments) {
    (void)runtime_->inject(runtime::backend::InputBatch{.pilot_reports = assignments});
}

void RuntimeFacade::step_batch() {
    (void)runtime_->advance(runtime::backend::AdvanceRequest{});
}

std::vector<MissionCommandMaintainedBatchContract>
RuntimeFacade::get_mission_commands_maintained_batch(
    const std::vector<WorldEntityRef> &refs) const {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .refs = refs,
            .include_mission_commands = true,
        })
        .mission_commands;
}

std::vector<TaskOrderMaintainedBatchContract>
RuntimeFacade::get_task_orders_maintained_batch(const std::vector<WorldEntityRef> &refs) const {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .refs = refs,
            .include_task_orders = true,
        })
        .task_orders;
}

std::vector<LeaderIntentMaintainedBatchContract>
RuntimeFacade::get_leader_intents_maintained_batch(const std::vector<WorldEntityRef> &refs) const {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .refs = refs,
            .include_leader_intents = true,
        })
        .leader_intents;
}

std::vector<PilotReportMaintainedBatchContract>
RuntimeFacade::get_pilot_reports_maintained_batch(const std::vector<WorldEntityRef> &refs) const {
    return runtime_
        ->export_state(runtime::backend::ExportRequest{
            .refs = refs,
            .include_pilot_reports = true,
        })
        .pilot_reports;
}
