#include "interfaces/python/bindings_runtime_detail.h"

// Orchestration shell: the per-domain slices below are registered in the
// exact order the single pre-split bind_runtime() used.  nanobind resolves
// later signatures against earlier registrations, so this sequence is fixed.
void bind_runtime(nb::module_ &m) {
    bind_runtime_shared_order(m, true);
}
