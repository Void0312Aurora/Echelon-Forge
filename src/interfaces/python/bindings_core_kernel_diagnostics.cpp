#include "interfaces/python/bindings_core_detail.h"

// Sub-orchestration shell for the diagnostics-only introspection surface: the
// sub-slices below chain their .def() calls onto the class in the exact order
// the single pre-split surface function used, so this sequence is fixed.
void bind_simulation_kernel_diagnostics_introspection_surface(
    nb::class_<SimulationKernel> &kernel) {
    bind_simulation_kernel_diagnostics_hit_and_view_surface(kernel);
    bind_simulation_kernel_diagnostics_platform_state_surface(kernel);
    bind_simulation_kernel_diagnostics_missile_runtime_surface(kernel);
}
