#pragma once

#include "interfaces/python/binding_utils.h"

// Per-domain slices of bind_episode().
//
// bindings_episode.cpp calls these in the order declared below.  That order is
// the module's nanobind type-registration order: a signature registered later
// resolves against the types registered before it, so the sequence is part of
// the Python-facing contract and must not be reordered.
void bind_episode_geometry(nb::module_ &m);
void bind_episode_mission_nav(nb::module_ &m);
void bind_episode_waypoint_approach(nb::module_ &m);
void bind_episode_flight_shaping(nb::module_ &m);
void bind_episode_objective(nb::module_ &m);
void bind_episode_termination(nb::module_ &m);
void bind_episode_execution_runtime(nb::module_ &m);
void bind_episode_state_batch(nb::module_ &m);
