#pragma once

#include "interfaces/python/binding_utils.h"

// Per-domain slices of bind_runtime().
//
// bindings_runtime.cpp calls these in the order declared below.  That order is
// the module's nanobind type-registration order: a signature registered later
// resolves against the types registered before it, so the sequence is part of
// the Python-facing contract and must not be reordered.
void bind_runtime_runtime(nb::module_ &m);
void bind_runtime_fidelity(nb::module_ &m);
void bind_runtime_platform(nb::module_ &m);
void bind_runtime_engagement(nb::module_ &m);
void bind_runtime_kill_chain(nb::module_ &m);
void bind_runtime_policy(nb::module_ &m);
void bind_runtime_batch_setup(nb::module_ &m);
void bind_runtime_experiment(nb::module_ &m);
void bind_runtime_batch_request(nb::module_ &m);
void bind_runtime_learning(nb::module_ &m);
void bind_runtime_batch_packet(nb::module_ &m);
void bind_runtime_tasking(nb::module_ &m);
void bind_runtime_window(nb::module_ &m);
void bind_runtime_counterfactual(nb::module_ &m);
void bind_runtime_platform_world(nb::module_ &m);
void bind_runtime_tasking_world(nb::module_ &m);
void bind_runtime_engine(nb::module_ &m);
void bind_runtime_facade(nb::module_ &m);
