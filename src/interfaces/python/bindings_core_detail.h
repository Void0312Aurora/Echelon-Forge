#pragma once

#include "interfaces/python/binding_utils.h"

#include <cstdint>
#include <utility>

#include <flecs.h>

#include "core/engine/simulation_kernel.h"

// Shared members of the pre-split bindings_core.cpp anonymous namespace.
//
// The debug-view structs and the two diagnostics quarantine helpers below are
// used by more than one slice, so they sit here at namespace scope instead of
// in a per-translation-unit anonymous namespace: nanobind resolves registered
// types through typeid, and an anonymous namespace in a header would hand each
// translation unit its own distinct type.

struct SensorDebugView {
    double max_range = 0.0;
    double detection_prob = 0.0;
    double reference_snr_db = 0.0;
    double reference_range_m = 0.0;
    double reference_rcs_m2 = 0.0;
    double pfa = 0.0;
    int confirm_hits_m = 0;
    int confirm_window_n = 0;
    double bearing_noise_std = 0.0;
    double range_noise_std = 0.0;
    double velocity_noise_std = 0.0;
    double alpha_beta_alpha = 0.0;
    double alpha_beta_beta = 0.0;
    double range_power = 0.0;
    double track_memory_s = 0.0;
    int type = 0;
};

struct TrackDebugView {
    uint64_t id = 0;
    uint64_t entity_id = 0;
    int status = 0;
    int usability = 0;
    int source = 0;
    int classification = 0;
    double quality = 0.0;
    double confidence = 0.0;
    bool iff_known = false;
    double classification_confidence = 0.0;
    double time_since_update = 0.0;
    double last_local_update_time = -1.0;
    double last_datalink_update_time = -1.0;
    int confirm_hit_count = 0;
    int confirm_miss_count = 0;
    int confirm_window_progress = 0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    double range = 0.0;
    double azimuth = 0.0;
    double elevation = 0.0;
};

struct FlightDynamicsDebugView {
    double max_speed = 0.0;
    double max_turn_rate = 0.0;
    double max_accel = 0.0;
    double max_climb_rate = 0.0;
    double max_g = 0.0;
    double alpha_dot_dps = 0.0;
    double stall_progress = 0.0;
    bool is_stalled = false;
    bool pitch_break_active = false;
    double time_in_stall_s = 0.0;
    double throttle_command = 0.0;
    double throttle_state = 0.0;
    double ab_state = 0.0;
    bool afterburner_active = false;
    double current_tsfc = 0.0;
    double current_thrust_n = 0.0;
    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;
    double fuel_leak_rate_kg_s = 0.0;
    double elevator_cmd = 0.0;
    double aileron_cmd = 0.0;
    double rudder_cmd = 0.0;
    double elevator_deflection = 0.0;
    double aileron_deflection = 0.0;
    double rudder_deflection = 0.0;
};

struct DiagnosticsLegacyEntityLease {
    SimulationKernel::WorldLease world_lease;
    flecs::entity entity;
};

inline DiagnosticsLegacyEntityLease
diagnostics_legacy_binding_entity_quarantine_lookup(SimulationKernel &self, uint64_t entity_id) {
    // WP22-R3 quarantine marker: raw entity binding access must stay localized
    // to diagnostics/legacy helpers while the lease keeps that access valid.
    auto world_lease = self.acquire_world_lease();
    auto entity = world_lease.world().entity(entity_id);
    return {std::move(world_lease), entity};
}

inline void diagnostics_mark_read_only_snapshot(nb::dict &out, const char *diagnostics_surface_kind,
                                                const char *runtime_owner_kind) {
    out["diagnostics_only"] = true;
    out["quarantined_surface"] = true;
    out["read_only_snapshot"] = true;
    out["maintained_truth"] = false;
    out["diagnostics_quarantine_marker"] = "read_only_diagnostics_quarantine";
    out["diagnostics_surface_kind"] = diagnostics_surface_kind;
    out["runtime_owner_kind"] = runtime_owner_kind;
}

// Per-domain slices of bind_core().
//
// bindings_core.cpp calls these in the order declared below.  That order is
// the module's nanobind type-registration order: a signature registered later
// resolves against the types registered before it, so the sequence is part of
// the Python-facing contract and must not be reordered.
void bind_core_enums(nb::module_ &m);
void bind_core_instruments(nb::module_ &m);
void bind_core_weapon_profiles(nb::module_ &m);
void bind_core_unit_data(nb::module_ &m);
void bind_core_debug_views(nb::module_ &m);
void bind_core_observation(nb::module_ &m);
void bind_core_simulation_kernel(nb::module_ &m);

// SimulationKernel method-surface slices.
//
// bindings_core_simulation_kernel.cpp calls these in the order declared below,
// which is the order the single pre-split bind_core() used.  The maintained /
// diagnostics / legacy / override boundary is the explicit quarantine split and
// the call order is the method-registration order, so neither may be reordered.
void bind_simulation_kernel_maintained_surface(nb::class_<SimulationKernel> &kernel);
void bind_simulation_kernel_diagnostics_introspection_surface(nb::class_<SimulationKernel> &kernel);
void bind_simulation_kernel_legacy_compatibility_debug_surface(
    nb::class_<SimulationKernel> &kernel);
void bind_simulation_kernel_diagnostics_override_surface(nb::class_<SimulationKernel> &kernel);

// Diagnostics-introspection sub-slices.
//
// bindings_core_kernel_diagnostics.cpp calls these in the order declared below,
// which is the order the single pre-split diagnostics surface chained them onto
// the class.  Same registration-order contract as above.
void bind_simulation_kernel_diagnostics_hit_and_view_surface(nb::class_<SimulationKernel> &kernel);
void bind_simulation_kernel_diagnostics_platform_state_surface(
    nb::class_<SimulationKernel> &kernel);
void bind_simulation_kernel_diagnostics_missile_runtime_surface(
    nb::class_<SimulationKernel> &kernel);
