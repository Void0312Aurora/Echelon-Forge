#include "interfaces/python/bindings_runtime_detail.h"

// Keep the maintained DTO registration order while omitting the raw
// WorldBatchRuntime binding. GPU helpers and SimulationKernel are likewise
// absent from the production module and remain diagnostics-only.
void bind_runtime_facade_only(nb::module_ &m) {
    bind_runtime_shared_order(m, false);
}
