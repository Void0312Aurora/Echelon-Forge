#include "interfaces/python/bindings_command_detail.h"

// Orchestration shell: the per-domain slices below are registered in the
// exact order the single pre-split bind_command() used.  nanobind resolves
// later signatures against earlier registrations, so this sequence is fixed.
void bind_command(nb::module_ &m) {
    bind_command_enums(m);
    bind_command_comm(m);
    bind_command_pilot_report(m);
    bind_command_pilot_action(m);
    bind_command_mission_command(m);
    bind_command_task_order(m);
    bind_command_task_order_api(m);
    bind_command_leader_intent(m);
}
