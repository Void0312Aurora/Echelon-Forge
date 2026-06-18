#include "runtime/facade/runtime_facade_internal.h"

#include <vector>

void RuntimeFacade::set_pilot_actions_batch(
    const std::vector<WorldPilotActionAssignment> &assignments) {
    runtime_->set_pilot_actions_batch(assignments);
}

std::vector<LaunchEvent>
RuntimeFacade::apply_launch_requests_batch(const std::vector<LaunchRequest> &requests) {
    return runtime_->apply_launch_requests_batch(requests);
}

void RuntimeFacade::set_mission_commands_maintained_batch(
    const std::vector<WorldMissionCommandMaintainedAssignment> &assignments) {
    runtime_->set_mission_commands_maintained_batch(assignments);
}

void RuntimeFacade::set_task_orders_maintained_batch(
    const std::vector<WorldTaskOrderMaintainedAssignment> &assignments) {
    runtime_->set_task_orders_maintained_batch(assignments);
}

void RuntimeFacade::set_leader_intents_maintained_batch(
    const std::vector<WorldLeaderIntentMaintainedAssignment> &assignments) {
    runtime_->set_leader_intents_maintained_batch(assignments);
}

void RuntimeFacade::set_pilot_reports_maintained_batch(
    const std::vector<WorldPilotReportMaintainedAssignment> &assignments) {
    runtime_->set_pilot_reports_maintained_batch(assignments);
}

void RuntimeFacade::step_batch() {
    runtime_->step_batch();
}

std::vector<MissionCommandMaintainedBatchContract>
RuntimeFacade::get_mission_commands_maintained_batch(
    const std::vector<WorldEntityRef> &refs) const {
    return runtime_->get_mission_commands_maintained_batch(refs);
}

std::vector<TaskOrderMaintainedBatchContract>
RuntimeFacade::get_task_orders_maintained_batch(const std::vector<WorldEntityRef> &refs) const {
    return runtime_->get_task_orders_maintained_batch(refs);
}

std::vector<LeaderIntentMaintainedBatchContract>
RuntimeFacade::get_leader_intents_maintained_batch(const std::vector<WorldEntityRef> &refs) const {
    return runtime_->get_leader_intents_maintained_batch(refs);
}

std::vector<PilotReportMaintainedBatchContract>
RuntimeFacade::get_pilot_reports_maintained_batch(const std::vector<WorldEntityRef> &refs) const {
    return runtime_->get_pilot_reports_maintained_batch(refs);
}
