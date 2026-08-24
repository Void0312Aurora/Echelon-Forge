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

void bind_command_pilot_action(nb::module_ &m) {
    // Bind PilotAction
    nb::class_<PilotAction>(m, "PilotAction")
        .def(nb::init<>())
        .def_rw("stick_pitch", &PilotAction::stick_pitch)
        .def_rw("stick_roll", &PilotAction::stick_roll)
        .def_rw("rudder", &PilotAction::rudder)
        .def_rw("throttle", &PilotAction::throttle)
        .def_rw("gear_handle", &PilotAction::gear_handle)
        .def_rw("flaps", &PilotAction::flaps)
        .def_rw("speedbrake", &PilotAction::speedbrake)
        .def_rw("brake", &PilotAction::brake)
        .def_rw("brake_left", &PilotAction::brake_left)
        .def_rw("brake_right", &PilotAction::brake_right)
        .def_rw("radar_active", &PilotAction::radar_active)
        .def_rw("radar_scan_az", &PilotAction::radar_scan_az)
        .def_rw("radar_scan_el", &PilotAction::radar_scan_el)
        .def_rw("tms_up", &PilotAction::tms_up)
        .def_rw("master_arm", &PilotAction::master_arm)
        .def_rw("fire_weapon", &PilotAction::fire_weapon)
        .def_rw("fire_gun", &PilotAction::fire_gun)
        .def_rw("weapon_select_id", &PilotAction::weapon_select_id)
        .def_rw("jettison_emergency", &PilotAction::jettison_emergency)
        .def_rw("program_chaff", &PilotAction::program_chaff)
        .def_rw("program_flare", &PilotAction::program_flare)
        .def_rw("active", &PilotAction::active);
}
