#include "interfaces/python/bindings_core_detail.h"

void bind_core_simulation_kernel(nb::module_ &m) {
    m.attr("DEFAULT_TIME_STEP_S") = SimulationKernel::kDefaultTimeStepS;
    nb::class_<SimulationKernel> simulation_kernel(m, "SimulationKernel");
    simulation_kernel.def(nb::init<>());

    // Maintained SimulationKernel API surface unless a narrower guard marker
    // below explicitly quarantines a diagnostics-only or legacy binding.
    bind_simulation_kernel_maintained_surface(simulation_kernel);
    // Diagnostics-only introspection surface. Keep additions explicit in the
    // WP22-E binding guard allowlist instead of widening maintained API by default.
    bind_simulation_kernel_diagnostics_introspection_surface(simulation_kernel);
    // Legacy compatibility debug surface. This remains quarantined until the
    // movement-command retirement stream owns a replacement or deletion path.
    bind_simulation_kernel_legacy_compatibility_debug_surface(simulation_kernel);
    // Diagnostics override surface. These helpers intentionally bypass the
    // maintained API contract and must stay on an explicit allowlist.
    bind_simulation_kernel_diagnostics_override_surface(simulation_kernel);
    // Ground native-probe surface. Tooling for the native_probe_only Ground
    // slice; every name stays on the WP22-E native-probe allowlist until a
    // reviewed Ground owner package replaces it with a facade/contract.
    bind_simulation_kernel_diagnostics_ground_native_probe_surface(simulation_kernel);
}
