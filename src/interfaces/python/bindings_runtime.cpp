#include "interfaces/python/bindings_runtime_detail.h"

// Orchestration shell: the per-domain slices below are registered in the
// exact order the single pre-split bind_runtime() used.  nanobind resolves
// later signatures against earlier registrations, so this sequence is fixed.
void bind_runtime(nb::module_ &m) {
    bind_runtime_runtime(m);
    bind_runtime_fidelity(m);
    bind_runtime_platform(m);
    bind_runtime_engagement(m);
    bind_runtime_kill_chain(m);
    bind_runtime_policy(m);
    bind_runtime_batch_setup(m);
    bind_runtime_experiment(m);
    bind_runtime_batch_request(m);
    bind_runtime_learning(m);
    bind_runtime_batch_packet(m);
    bind_runtime_tasking(m);
    bind_runtime_window(m);
    bind_runtime_platform_world(m);
    bind_runtime_tasking_world(m);
    bind_runtime_engine(m);
    bind_runtime_facade(m);
}
