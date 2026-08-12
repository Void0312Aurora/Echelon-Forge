#pragma once

#include "interfaces/python/binding_utils.h"

// Per-domain slices of bind_command().
//
// bindings_command.cpp calls these in the order declared below.  That order is
// the module's nanobind type-registration order: a signature registered later
// resolves against the types registered before it, so the sequence is part of
// the Python-facing contract and must not be reordered.
void bind_command_enums(nb::module_ &m);
void bind_command_comm(nb::module_ &m);
void bind_command_pilot_report(nb::module_ &m);
void bind_command_pilot_action(nb::module_ &m);
void bind_command_mission_command(nb::module_ &m);
void bind_command_task_order(nb::module_ &m);
void bind_command_task_order_api(nb::module_ &m);
void bind_command_leader_intent(nb::module_ &m);
