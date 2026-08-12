#include "interfaces/python/bindings_command_detail.h"

#include "components/command/common/comm_message.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/systems/comm.h"
#include "components/domains/air/tasking/air_tasking_enums.h"
#include "components/tasking/common/core_tasking_enums.h"
#include "components/domains/ground/tasking/ground_tasking_enums.h"
#include "components/tasking/leader_intent.h"
#include "components/domains/naval/tasking/naval_tasking_enums.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"
#include "runtime/contracts/world_batch_contracts.h"

void bind_command_task_order_api(nb::module_ &m) {
    m.def(
        "task_order_shared_core",
        [](nb::handle order_obj) {
            auto &order = nb::cast<TaskOrder &>(order_obj);
            return nb::inst_reference(nb::type<TaskOrderCore>(), &task_order_shared_core(order),
                                      order_obj);
        },
        nb::arg("order"));
    m.def(
        "task_order_shared_core_directive",
        [](const TaskOrder &order) { return task_order_shared_core_directive(order); },
        nb::arg("order"));
    m.def(
        "task_order_air_owner_slice",
        [](nb::handle order_obj) {
            auto &order = nb::cast<TaskOrder &>(order_obj);
            return nb::inst_reference(nb::type<TaskOrderAir>(), &task_order_air_owner_slice(order),
                                      order_obj);
        },
        nb::arg("order"));
    m.def(
        "task_order_naval_owner_slice",
        [](nb::handle order_obj) {
            auto &order = nb::cast<TaskOrder &>(order_obj);
            return nb::inst_reference(nb::type<TaskOrderNaval>(),
                                      &task_order_naval_owner_slice(order), order_obj);
        },
        nb::arg("order"));
    m.def(
        "task_order_ground_owner_slice",
        [](nb::handle order_obj) {
            auto &order = nb::cast<TaskOrder &>(order_obj);
            return nb::inst_reference(nb::type<TaskOrderGround>(),
                                      &task_order_ground_owner_slice(order), order_obj);
        },
        nb::arg("order"));
    m.def(
        "task_order_air_recovery_directive",
        [](const TaskOrder &order) { return task_order_air_recovery_directive(order); },
        nb::arg("order"));
    m.def(
        "task_order_air_tasking_identity_directive",
        [](const TaskOrder &order) { return task_order_air_tasking_identity_directive(order); },
        nb::arg("order"));
    m.def(
        "task_order_air_stationing_directive",
        [](const TaskOrder &order) { return task_order_air_stationing_directive(order); },
        nb::arg("order"));
    m.def(
        "task_order_air_takeoff_directive",
        [](const TaskOrder &order) { return task_order_air_takeoff_directive(order); },
        nb::arg("order"));
    m.def(
        "task_order_air_formation_directive",
        [](const TaskOrder &order) { return task_order_air_formation_directive(order); },
        nb::arg("order"));
    m.def(
        "task_order_naval_command_authority",
        [](const TaskOrder &order) { return task_order_naval_command_authority(order); },
        nb::arg("order"));
    m.def(
        "task_order_naval_stationing_directive",
        [](const TaskOrder &order) { return task_order_naval_stationing_directive(order); },
        nb::arg("order"));
    m.def(
        "task_order_ground_static_task_directive",
        [](const TaskOrder &order) { return task_order_ground_static_task_directive(order); },
        nb::arg("order"));
    m.def(
        "task_order_maintained_batch_contract",
        [](const TaskOrder &order) { return task_order_maintained_batch_contract(order); },
        nb::arg("order"));
    m.def(
        "task_order_compatibility_shell_from_maintained_batch_contract",
        [](nb::handle contract_obj) {
            const auto &contract = nb::cast<const TaskOrderMaintainedBatchContract &>(contract_obj);
            return task_order_compatibility_shell_from_maintained_batch_contract(contract);
        },
        nb::arg("contract"));
    m.def(
        "apply_task_order_maintained_batch_contract_to_compatibility_shell",
        [](nb::handle order_obj, nb::handle contract_obj) {
            auto &order = nb::cast<TaskOrder &>(order_obj);
            const auto &contract = nb::cast<const TaskOrderMaintainedBatchContract &>(contract_obj);
            apply_task_order_maintained_batch_contract_to_compatibility_shell(order, contract);
        },
        nb::arg("order"), nb::arg("contract"));
    m.def(
        "task_order_maintained_air_tasking_identity",
        [](nb::handle contract_obj) {
            auto &contract = nb::cast<TaskOrderMaintainedBatchContract &>(contract_obj);
            return nb::inst_reference(nb::type<TaskOrderAirTaskingIdentityDirective>(),
                                      &contract.air_tasking_identity, contract_obj);
        },
        nb::arg("contract"));
    m.def(
        "task_order_maintained_air_stationing",
        [](nb::handle contract_obj) {
            auto &contract = nb::cast<TaskOrderMaintainedBatchContract &>(contract_obj);
            return nb::inst_reference(nb::type<TaskOrderAirStationingDirective>(),
                                      &contract.air_stationing, contract_obj);
        },
        nb::arg("contract"));
    m.def(
        "task_order_maintained_air_formation",
        [](nb::handle contract_obj) {
            auto &contract = nb::cast<TaskOrderMaintainedBatchContract &>(contract_obj);
            return nb::inst_reference(nb::type<TaskOrderAirFormationDirective>(),
                                      &contract.air_formation, contract_obj);
        },
        nb::arg("contract"));
    m.def(
        "task_order_maintained_naval_stationing",
        [](nb::handle contract_obj) {
            auto &contract = nb::cast<TaskOrderMaintainedBatchContract &>(contract_obj);
            return nb::inst_reference(nb::type<TaskOrderNavalStationingDirective>(),
                                      &contract.naval_stationing, contract_obj);
        },
        nb::arg("contract"));
    m.def(
        "task_order_maintained_ground_static_task",
        [](nb::handle contract_obj) {
            auto &contract = nb::cast<TaskOrderMaintainedBatchContract &>(contract_obj);
            return nb::inst_reference(nb::type<TaskOrderGround::StaticTaskDirective>(),
                                      &contract.ground_static_task, contract_obj);
        },
        nb::arg("contract"));
}
