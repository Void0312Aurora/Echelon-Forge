#include "interfaces/python/bindings_episode_detail.h"

// Orchestration shell: the per-domain slices below are registered in the
// exact order the single pre-split bind_episode() used.  nanobind resolves
// later signatures against earlier registrations, so this sequence is fixed.
void bind_episode(nb::module_ &m) {
    bind_episode_geometry(m);
    bind_episode_mission_nav(m);
    bind_episode_waypoint_approach(m);
    bind_episode_flight_shaping(m);
    bind_episode_objective(m);
    bind_episode_termination(m);
    bind_episode_execution_runtime(m);
    bind_episode_state_batch(m);
}
