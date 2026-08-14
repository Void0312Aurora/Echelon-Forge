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

void bind_command_comm(nb::module_ &m) {
    nb::class_<CommPacket>(m, "CommPacket")
        .def(nb::init<>())
        .def_rw("sender_id", &CommPacket::sender_id)
        .def_rw("target_receiver_id", &CommPacket::target_receiver_id)
        .def_rw("type", &CommPacket::type)
        .def_rw("entity_ref", &CommPacket::entity_ref)
        .def_rw("location_x", &CommPacket::location_x)
        .def_rw("location_y", &CommPacket::location_y)
        .def_rw("location_z", &CommPacket::location_z)
        .def_rw("value", &CommPacket::value)
        .def_rw("status_code", &CommPacket::status_code)
        .def_rw("timestamp", &CommPacket::timestamp);
}
