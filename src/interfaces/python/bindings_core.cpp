#include "interfaces/python/bindings_core_detail.h"

// Orchestration shell: the per-domain slices below are registered in the
// exact order the single pre-split bind_core() used.  nanobind resolves
// later signatures against earlier registrations, so this sequence is fixed.
void bind_core(nb::module_ &m) {
    bind_core_enums(m);
    bind_core_instruments(m);
    bind_core_weapon_profiles(m);
    bind_core_unit_data(m);
    bind_core_debug_views(m);
    bind_core_observation(m);
    bind_core_simulation_kernel(m);
}
