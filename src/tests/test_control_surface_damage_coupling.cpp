// M5 mechanism regression: battle damage acts on CONTROL-SURFACE EFFECTIVENESS.
//
// Subproject: docs/task/air_combat/flight_control_surface_model/
//
// The control-surface model moved the damage coupling from a downstream torque
// scale to the physical surface path: a degraded surface (reduced
// *_control_integrity) physically produces less control moment through the
// effectiveness derivatives in the aerodynamics system
// (Cm += pitch_authority * ctrl_eff_scale * cm_delta_e * elevator_rad, etc).
//
// These doctests lock that semantics so it cannot silently regress back into a
// synthetic torque scale. They drive the real aerodynamics system over a fixed
// flight state with a fixed surface deflection and compare the produced body
// torque between an intact airframe and a damaged one.
//
// To ISOLATE the control-surface contribution from the rest of the moment model
// (Cm_alpha, Cm_q, sideslip-driven Cl/Cn, pitch-break), the test state pins
// alpha = 0, beta = 0, and zero body rates. With those zero, the only nonzero
// moment terms are the control-surface terms, so the torque delta between
// intact and damaged is attributable to the surface-effectiveness coupling.

#include "components/basic/common.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/physics/aero_tables.h"
#include "components/physics/control_surface.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/systems/logistics.h"
#include "core/engine/simulation_kernel.h"
#include "systems/domains/air/aerodynamics_system.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <cmath>

namespace {

// Use SimulationKernel's registered world to avoid Flecs component symbol
// collisions, but run only the Aerodynamics stage so AeroState and
// ControlSurfaceState remain the fixed probe inputs.
struct TorqueProbe {
    double pitch_torque = 0.0;
    double roll_torque = 0.0;
    double yaw_torque = 0.0;
};

TorqueProbe run_surface_torque_probe(double elevator_pos, double aileron_pos, double rudder_pos,
                                     double pitch_integrity, double roll_integrity,
                                     double yaw_integrity) {
    SimulationKernel kernel;
    flecs::world &world = kernel.get_world();

    AeroState aero{};
    aero.dynamic_pressure = 20000.0; // well above the q<0.1 skip guard
    aero.angle_of_attack = 0.0;      // isolate: no Cm_alpha contribution
    aero.sideslip_angle = 0.0;       // isolate: no sideslip Cl/Cn contribution
    aero.mach_number = 0.3;
    aero.stall_progress = 0.0;

    MassProperties props{};
    props.reference_area_m2 = 28.0;
    props.wing_span_m = 9.45;
    props.chord_m = 3.45;

    Velocity vel{};
    // Heading 0 is north (+Y). Keep velocity aligned with heading so
    // ComputeAeroState preserves beta=0 instead of generating sideslip moments
    // that could masquerade as roll/yaw surface effects.
    vel.vx = 0.0;
    vel.vy = 200.0;
    vel.vz = 0.0;

    Transform tf{};
    tf.heading = 0.0;
    tf.pitch = 0.0;
    tf.roll = 0.0;
    tf.x = 0.0;
    tf.y = 0.0;
    tf.z = 5000.0; // high AGL: no ground-effect interaction

    AngularVelocity ang{}; // zero rates: no Cm_q / Cl_p / Cn_r damping terms

    ControlSurfaceState surfaces{};
    surfaces.elevator_cmd = elevator_pos;
    surfaces.aileron_cmd = aileron_pos;
    surfaces.rudder_cmd = rudder_pos;
    surfaces.elevator_pos = elevator_pos;
    surfaces.aileron_pos = aileron_pos;
    surfaces.rudder_pos = rudder_pos;

    AircraftDamageState damage{};
    damage.pitch_control_integrity = pitch_integrity;
    damage.roll_control_integrity = roll_integrity;
    damage.yaw_control_integrity = yaw_integrity;
    // Keep every other integrity at the struct default (1.0) so control_path = 1.

    auto e = world.entity()
                 .set<KeyEntity>({UnitType::Aircraft})
                 .set<ForceAccumulator>({})
                 .set<AeroState>(aero)
                 .set<MassProperties>(props)
                 .set<Velocity>(vel)
                 .set<Transform>(tf)
                 .set<AngularVelocity>(ang)
                 .set<ControlSurfaceState>(surfaces)
                 .set<AircraftDamageState>(damage);

    REQUIRE(kernel.run_exact_stage_direct("ComputeAerodynamics"));

    TorqueProbe out;
    if (const ForceAccumulator *f = e.get<ForceAccumulator>()) {
        out.pitch_torque = f->torque_pitch;
        out.roll_torque = f->torque_roll;
        out.yaw_torque = f->torque_yaw;
    }
    return out;
}

} // namespace

TEST_CASE("M5: intact elevator produces a nonzero pitch moment from deflection") {
    const TorqueProbe intact = run_surface_torque_probe(0.5, 0.0, 0.0, 1.0, 1.0, 1.0);
    // A positive elevator deflection must produce a real (nonzero) pitch moment
    // through the effectiveness derivative; this is the baseline the damage
    // cases scale down from.
    CHECK(std::abs(intact.pitch_torque) > 1.0);
}

TEST_CASE("M5: degraded pitch control integrity reduces elevator pitch moment") {
    const TorqueProbe intact = run_surface_torque_probe(0.5, 0.0, 0.0, 1.0, 1.0, 1.0);
    const TorqueProbe damaged = run_surface_torque_probe(0.5, 0.0, 0.0, 0.25, 1.0, 1.0);

    // Same deflection, same flight state: the only difference is pitch-control
    // damage. The damaged airframe must produce strictly less pitch moment,
    // because damage now acts on surface effectiveness (pitch_authority) rather
    // than being ignored or applied elsewhere.
    CHECK(std::abs(damaged.pitch_torque) < std::abs(intact.pitch_torque));
    // And it must still produce SOME moment (authority is floored, not zeroed):
    CHECK(std::abs(damaged.pitch_torque) > 0.0);
}

TEST_CASE("M5: degraded roll control integrity reduces aileron roll moment") {
    const TorqueProbe intact = run_surface_torque_probe(0.0, 0.5, 0.0, 1.0, 1.0, 1.0);
    const TorqueProbe damaged = run_surface_torque_probe(0.0, 0.5, 0.0, 1.0, 0.25, 1.0);
    const TorqueProbe no_surface = run_surface_torque_probe(0.0, 0.0, 0.0, 1.0, 0.25, 1.0);

    CHECK(std::abs(damaged.roll_torque) < std::abs(intact.roll_torque));
    CHECK(std::abs(damaged.roll_torque) > 0.0);
    CHECK(std::abs(no_surface.roll_torque) < 1.0e-6);
}

TEST_CASE("M5: degraded yaw control integrity reduces rudder yaw moment") {
    const TorqueProbe intact = run_surface_torque_probe(0.0, 0.0, 0.5, 1.0, 1.0, 1.0);
    const TorqueProbe damaged = run_surface_torque_probe(0.0, 0.0, 0.5, 1.0, 1.0, 0.25);
    const TorqueProbe no_surface = run_surface_torque_probe(0.0, 0.0, 0.0, 1.0, 1.0, 0.25);

    CHECK(std::abs(damaged.yaw_torque) < std::abs(intact.yaw_torque));
    CHECK(std::abs(damaged.yaw_torque) > 0.0);
    CHECK(std::abs(no_surface.yaw_torque) < 1.0e-6);
}
