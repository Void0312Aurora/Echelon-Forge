#include "interfaces/python/bindings_runtime_detail.h"

// Sub-orchestration shell: the per-domain slices below are registered in
// the exact order the single pre-split bind_runtime_engagement() used.
// nanobind resolves later signatures against earlier registrations, so this
// sequence is fixed.
void bind_runtime_engagement(nb::module_ &m) {
    bind_runtime_engagement_events(m);
    bind_runtime_engagement_damage(m);
    bind_runtime_engagement_track_launch(m);
    bind_runtime_engagement_munition(m);
}
