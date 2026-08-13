#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include <spdlog/spdlog.h>

#include "core/engine/world_batch_runtime.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/fidelity_profile_contracts.h"
#include "runtime/contracts/platform_capability_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/facade/runtime_facade.h"

void bind_runtime_tasking_world(nb::module_ &m) {
    nb::class_<WorldPilotActionAssignment> world_pilot_action_assignment_class(
        m, "WorldPilotActionAssignment");
    world_pilot_action_assignment_class.def(nb::init<>());
#define EF_WORLD_PILOT_ACTION_ASSIGNMENT_FIELD(type, name, default_value)                          \
    world_pilot_action_assignment_class.def_rw(#name, &WorldPilotActionAssignment::name);
#include "runtime/contracts/detail/tasking/world_pilot_action_assignment.inc"

    nb::class_<WorldMissionCommandAssignment> world_mission_command_assignment_class(
        m, "WorldMissionCommandAssignment");
    world_mission_command_assignment_class.def(nb::init<>());
#define EF_WORLD_MISSION_COMMAND_ASSIGNMENT_FIELD(type, name, default_value)                       \
    world_mission_command_assignment_class.def_rw(#name, &WorldMissionCommandAssignment::name);
#include "runtime/contracts/detail/tasking/world_mission_command_assignment.inc"

    nb::class_<WorldMissionCommandMaintainedAssignment>
        world_mission_command_maintained_assignment_class(
            m, "WorldMissionCommandMaintainedAssignment");
    world_mission_command_maintained_assignment_class.def(nb::init<>());
#define EF_WORLD_MISSION_COMMAND_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value)            \
    world_mission_command_maintained_assignment_class.def_rw(                                      \
        #name, &WorldMissionCommandMaintainedAssignment::name);
#include "runtime/contracts/detail/tasking/world_mission_command_maintained_assignment.inc"

    nb::class_<WorldTaskOrderMaintainedAssignment> world_task_order_maintained_assignment_class(
        m, "WorldTaskOrderMaintainedAssignment");
    world_task_order_maintained_assignment_class.def(nb::init<>());
#define EF_WORLD_TASK_ORDER_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value)                 \
    world_task_order_maintained_assignment_class.def_rw(                                           \
        #name, &WorldTaskOrderMaintainedAssignment::name);
#include "runtime/contracts/detail/tasking/world_task_order_maintained_assignment.inc"

    nb::class_<WorldLeaderIntentAssignment> world_leader_intent_assignment_class(
        m, "WorldLeaderIntentAssignment");
    world_leader_intent_assignment_class.def(nb::init<>());
#define EF_WORLD_LEADER_INTENT_ASSIGNMENT_FIELD(type, name, default_value)                         \
    world_leader_intent_assignment_class.def_rw(#name, &WorldLeaderIntentAssignment::name);
#include "runtime/contracts/detail/tasking/world_leader_intent_assignment.inc"

    nb::class_<WorldLeaderIntentMaintainedAssignment>
        world_leader_intent_maintained_assignment_class(m, "WorldLeaderIntentMaintainedAssignment");
    world_leader_intent_maintained_assignment_class.def(nb::init<>());
#define EF_WORLD_LEADER_INTENT_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value)              \
    world_leader_intent_maintained_assignment_class.def_rw(                                        \
        #name, &WorldLeaderIntentMaintainedAssignment::name);
#include "runtime/contracts/detail/tasking/world_leader_intent_maintained_assignment.inc"

    nb::class_<WorldPilotReportAssignment> world_pilot_report_assignment_class(
        m, "WorldPilotReportAssignment");
    world_pilot_report_assignment_class.def(nb::init<>());
#define EF_WORLD_PILOT_REPORT_ASSIGNMENT_FIELD(type, name, default_value)                          \
    world_pilot_report_assignment_class.def_rw(#name, &WorldPilotReportAssignment::name);
#include "runtime/contracts/detail/tasking/world_pilot_report_assignment.inc"

    nb::class_<WorldPilotReportMaintainedAssignment> world_pilot_report_maintained_assignment_class(
        m, "WorldPilotReportMaintainedAssignment");
    world_pilot_report_maintained_assignment_class.def(nb::init<>());
#define EF_WORLD_PILOT_REPORT_MAINTAINED_ASSIGNMENT_FIELD(type, name, default_value)               \
    world_pilot_report_maintained_assignment_class.def_rw(                                         \
        #name, &WorldPilotReportMaintainedAssignment::name);
#include "runtime/contracts/detail/tasking/world_pilot_report_maintained_assignment.inc"
}
