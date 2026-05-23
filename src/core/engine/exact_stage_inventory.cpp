#include "simulation_kernel.h"

#include <algorithm>
#include <initializer_list>
#include <stdexcept>
#include <string_view>
#include <vector>

namespace {
std::vector<std::string> string_list(std::initializer_list<const char*> values) {
    std::vector<std::string> out;
    out.reserve(values.size());
    for (const char* value : values) {
        out.emplace_back(value);
    }
    return out;
}

const std::vector<ExactStepStageDescriptor>& exact_gpu_stage_inventory() {
    static const std::vector<ExactStepStageDescriptor> inventory = {
        {0, "RWR_Reset", "PreUpdate", "ew",
         "Clears transient RWR state before the sensor pass.",
         false, false},
        {1, "ClearCommInbox", "PreUpdate", "systems",
         "Prunes expired comm inbox entries before the update pass.",
         false, false},
        {2, "CommandLinkMovement", "OnUpdate", "command",
         "Delivers delayed typed control targets and refreshes optional compatibility movement mirrors.",
         true, true},
        {3, "CommandLinkAction", "OnUpdate", "command",
         "Delivers delayed action payloads while the pending shell stays quarantined.",
         true, true},
        {4, "CommandLinkMission", "OnUpdate", "command",
         "Delivers pending mission commands and advances queued mission intent.",
         true, true},
        {5, "ActionMapping", "OnUpdate", "command",
         "Maps normalized RL action inputs into typed control-state targets and optional movement mirrors.",
         true, true},
        {6, "CommandLag", "OnUpdate", "command",
         "Applies the exact lag filter to typed control targets and optional lagged mirrors.",
         true, true},
        {7, "FlightControl", "OnUpdate", "control",
         "Runs the control model from typed control-state inputs and refreshes control side effects.",
         true, true},
        {8, "ClearForces", "OnLoad", "physics",
         "Clears ForceAccumulator before exact force/torque buildup.",
         true, true},
        {9, "ComputeAeroState", "OnUpdate", "physics",
         "Refreshes air-relative dynamic pressure, Mach, AoA, and beta.",
         true, true},
        {10, "ComputeForces", "OnUpdate", "physics",
         "Adds gravity and propulsion forces from resolved propulsion state.",
         true, true},
        {11, "ComputeAerodynamics", "OnUpdate", "physics",
         "Adds aerodynamic force and torque surfaces from aero state.",
         true, true},
        {12, "GroundContact", "OnUpdate", "physics",
         "Applies ground reaction, braking, and steering from bridge-resolved ground control.",
         true, true},
        {13, "RotationalIntegrate", "OnUpdate", "physics",
         "Integrates angular rates and attitude from accumulated torques.",
         true, true},
        {14, "MissileGuidance", "OnUpdate", "combat",
         "Updates missile velocity guidance for active missiles.",
         true, true},
        {15, "LeapfrogIntegrate", "OnUpdate", "physics",
         "Advances translation with the exact force-driven leapfrog integrator.",
         true, true},
        {16, "NavigationSystem", "OnUpdate", "navigation",
         "Refreshes EGI/georeference outputs after integration.",
         true, true},
        {17, "SensorSystem", "OnUpdate", "sensor",
         "Runs the current sensor model and refreshes contact memory.",
         false, false},
        {18, "DataLinkFusionSystem", "OnUpdate", "systems",
         "Fuses shared contacts across active data-link peers.",
         false, false},
        {19, "UpdateInstruments", "OnUpdate", "observation",
         "Refreshes learner-facing instrument outputs from exact state and typed or mission projections.",
         true, true},
        {20, "ProximityFuze", "OnUpdate", "combat",
         "Applies missile fuze and hit-resolution side effects.",
         false, false},
        {21, "EW_Release_Chaff", "OnUpdate", "ew",
         "Spawns chaff expendables and updates countermeasure inventory.",
         false, false},
        {22, "EW_Release_Flare", "OnUpdate", "ew",
         "Spawns flare expendables and updates countermeasure inventory.",
         false, false},
        {23, "EW_Lifetime_Manager", "OnUpdate", "ew",
         "Ages and removes transient EW expendables.",
         false, false},
        {24, "FuelConsumption", "OnUpdate", "logistics",
         "Consumes fuel from propulsion runtime state and updates afterburner/fuel-flow state.",
         true, true},
        {25, "MassUpdate", "OnUpdate", "logistics",
         "Refreshes rigid-body total mass from the fuel system.",
         true, true},
        {26, "LogisticsAction", "OnUpdate", "logistics",
         "Applies jettison and logistics-triggered configuration changes.",
         false, false},
        {27, "ResupplyLogic", "OnUpdate", "logistics",
         "Handles refuel/rearm turnaround logic near logistics nodes.",
         false, false},
    };
    return inventory;
}

const std::vector<ExactStepStageContractDescriptor>& exact_gpu_stage_contract_inventory() {
    // Guarded contract ledger for exact-stage migration evidence. These entries
    // document typed owners, compatibility projections, and diagnostics shells
    // that the trace pipeline still exposes.
    // Keep legacy transport shells named as diagnostics/compatibility evidence,
    // never as maintained truth.
    // They are not maintained implementation truth by themselves.
    static const std::vector<ExactStepStageContractDescriptor> contracts = {
        {
            2, "CommandLinkMovement", "OnUpdate", "command", true, true,
            string_list({
                "MissionCommandControlState",
                "PendingMovementCommand.typed_command.control_state",
                "PendingMovementCommand.command (diagnostics shell)",
                "CommandLink",
                "world_time_total"
            }),
            string_list({
                "MissionCommandControlState",
                "PendingMovementCommand.active",
                "PendingMovementCommand.command (diagnostics shell)",
                "MovementCommand (optional compatibility projection)",
                "LaggedCommand (optional compatibility projection)"
            }),
            string_list({
                "packed.PendingMovementCommand",
                "packed.MovementCommand (optional projection)",
                "packed.LaggedCommand (optional projection)",
                "apply_signatures"
            }),
            string_list({}),
            "Apply delayed typed control-state targets once latency expires and refresh diagnostics/compatibility projections only when present.",
            "Guarded contract ledger entry: maintained delayed-delivery truth lands in MissionCommandControlState. PendingMovementCommand.command is a diagnostics shell, and optional MovementCommand/LaggedCommand projections remain compatibility evidence rather than maintained implementation truth."
        },
        {
            3, "CommandLinkAction", "OnUpdate", "command", true, true,
            string_list({
                "PendingActionCommand.command (diagnostics shell)",
                "PendingActionCommand.typed_air_control_bridge (overlay projection)",
                "PendingActionCommand.active",
                "CommandLink",
                "world_time_total"
            }),
            string_list({
                "ActionCommand",
                "PendingActionCommand.active",
                "PendingActionCommand.typed_air_control_bridge (overlay projection)",
                "MissionCommandControlState.typed_air_control (optional bridge projection)"
            }),
            string_list({
                "packed.ActionCommand",
                "packed.PendingActionCommand",
                "packed.PendingActionCommand.typed_air_control_bridge",
                "apply_signatures"
            }),
            string_list({"CommandLinkMovement"}),
            "Deliver queued action commands through the typed air-control overlay while keeping the pending shell quarantined.",
            "PendingActionCommand remains a quarantined legacy transport shell in this slice. Its typed_air_control_bridge is an overlay projection only; when MissionCommandControlState is already present, delivery refreshes the typed air-control overlay without claiming a full typed action replacement."
        },
        {
            4, "CommandLinkMission", "OnUpdate", "command", true, true,
            string_list({"PendingMissionCommand", "MissionCommandPendingQueue", "CommandLink", "world_time_total"}),
            string_list({"MissionCommand", "PendingMissionCommand.active", "MissionCommandPendingQueue"}),
            string_list({"packed.MissionCommand", "packed.PendingMissionCommand", "apply_signatures"}),
            string_list({"CommandLinkAction"}),
            "Deliver queued mission commands into the active mission surface and advance the pending queue.",
            "Mission intent remains first-class command truth here; the ledger keeps queue and transport state explicit rather than folding it into movement or action ownership claims."
        },
        {
            5, "ActionMapping", "OnUpdate", "command", true, true,
            string_list({
                "MissionCommandControlState",
                "ActionCommand",
                "ActionSpaceConfig",
                "Transform",
                "Velocity",
                "MovementCommand (optional compatibility projection)"
            }),
            string_list({"MissionCommandControlState", "MovementCommand (optional compatibility projection)"}),
            string_list({"packed.MovementCommand (optional projection)", "apply_signatures"}),
            string_list({"CommandLinkMission"}),
            "Map normalized RL actions onto typed control-state targets and refresh optional compatibility movement projections only.",
            "MissionCommandControlState is the maintained typed owner here. MovementCommand survives only as an optional bridge or trace projection for compatibility consumers."
        },
        {
            6, "CommandLag", "OnUpdate", "command", true, true,
            string_list({
                "MissionCommandControlState",
                "CommandLag",
                "Transform",
                "Velocity",
                "LaggedCommand (optional compatibility projection)"
            }),
            string_list({"MissionCommandControlState", "LaggedCommand (optional compatibility projection)"}),
            string_list({"packed.LaggedCommand (optional projection)", "apply_signatures"}),
            string_list({"ActionMapping"}),
            "Apply first-order lag to typed command-control targets and refresh optional compatibility lag projections only.",
            "Lagged command truth lives in MissionCommandControlState.lagged_* for maintained callers. LaggedCommand remains optional compatibility evidence for bridge consumers and exact-stage traces."
        },
        {
            7, "FlightControl", "OnUpdate", "control", true, true,
            string_list({
                "Velocity", "Transform", "MissionCommandControlState", "FlightModel",
                "PilotAction/MissionCommand via control-model fetch",
                "ControlModelRef", "EnvironmentModelRef"
            }),
            string_list({
                "Velocity", "Transform",
                "ForceAccumulator (model-owned side effects)",
                "ControlLawState (model-owned side effects)",
                "LandingGear (model-owned side effects)"
            }),
            string_list({
                "hidden_dynamics.force_accumulator",
                "hidden_dynamics.control_law_state",
                "packed.LandingGear",
                "apply_signatures"
            }),
            string_list({"CommandLag"}),
            "Run the exact control model from typed control-state inputs and refresh model-owned control side effects.",
            "The Flecs signature exposes MissionCommandControlState as the maintained typed owner. Additional PilotAction/MissionCommand reads and ForceAccumulator, ControlLawState, or LandingGear side effects happen inside the control-model update and stay documented here as contract evidence, not as standalone ownership claims."
        },
        {
            8, "ClearForces", "OnLoad", "physics", true, true,
            string_list({"ForceAccumulator"}),
            string_list({"ForceAccumulator"}),
            string_list({"hidden_dynamics.force_accumulator", "apply_signatures"}),
            string_list({"FlightControl"}),
            "Reset the per-frame force and torque accumulator before physics buildup.",
            "All downstream force-producing systems assume a clean accumulator; stale torque here invalidates every later dynamics stage."
        },
        {
            9, "ComputeAeroState", "OnUpdate", "physics", true, true,
            string_list({"AeroState", "Transform", "Velocity", "EnvironmentModelRef"}),
            string_list({"AeroState"}),
            string_list({"hidden_dynamics.aero_state", "apply_signatures"}),
            string_list({"ClearForces"}),
            "Refresh air-relative dynamic pressure, Mach, AoA, and sideslip.",
            "This stage carries forward the previous AeroState for low-speed blending, so replay must preserve the incoming cached angles as part of the contract."
        },
        {
            10, "ComputeForces", "OnUpdate", "physics", true, true,
            string_list({
                "ForceAccumulator", "Transform", "Velocity", "Mass", "Propulsion",
                "FlightModel", "PilotAction", "MissionCommandControlState"
            }),
            string_list({"ForceAccumulator"}),
            string_list({"hidden_dynamics.force_accumulator", "packed.Propulsion", "apply_signatures"}),
            string_list({"ComputeAeroState"}),
            "Accumulate gravity and thrust forces from the resolved propulsion state.",
            "Throttle and command priority are resolved upstream through MissionCommandControlState plus the typed air-control bridge and ComputePropulsion. This ledger must not be read as if MovementCommand or ActionCommand were maintained force-stage inputs."
        },
        {
            11, "ComputeAerodynamics", "OnUpdate", "physics", true, true,
            string_list({
                "ForceAccumulator", "AeroState", "MassProperties", "Velocity", "Transform",
                "LandingGear", "PilotAction", "AngularVelocity", "EnvironmentModelRef"
            }),
            string_list({"ForceAccumulator", "AeroState"}),
            string_list({"hidden_dynamics.force_accumulator", "hidden_dynamics.aero_state", "apply_signatures"}),
            string_list({"ComputeForces"}),
            "Add lift, drag, and aerodynamic moment surfaces from the refreshed aero state.",
            "This stage is the main producer of aerodynamic torques; exact parity requires matching both accumulator torques and cached lift/drag coefficients."
        },
        {
            12, "GroundContact", "OnUpdate", "physics", true, true,
            string_list({
                "ForceAccumulator", "Transform", "Velocity", "Mass", "GroundState",
                "LandingGear", "AngularVelocity", "PilotAction",
                "MissionCommandControlState", "GearState", "Health", "EnvironmentModelRef"
            }),
            string_list({"ForceAccumulator", "Velocity", "GroundState", "GearState", "Health"}),
            string_list({
                "hidden_dynamics.force_accumulator",
                "truth.vz",
                "packed.GroundState",
                "packed.GearState",
                "terminal"
            }),
            string_list({"ComputeAerodynamics"}),
            "Apply normal force, braking, steering, and ground-restoring torques from bridge-resolved ground control.",
            "Maintained ground-control semantics resolve through MissionCommandControlState and PilotAction via the air-control bridge. Legacy movement mirrors only survive upstream as optional compatibility projections."
        },
        {
            13, "RotationalIntegrate", "OnUpdate", "physics", true, true,
            string_list({"Transform", "AngularVelocity", "Inertia", "ForceAccumulator"}),
            string_list({"Transform", "AngularVelocity"}),
            string_list({
                "truth.heading", "truth.pitch", "truth.roll",
                "hidden_dynamics.angular_velocity",
                "apply_signatures"
            }),
            string_list({"GroundContact"}),
            "Integrate angular rates from accumulated torques and update Euler attitude.",
            "This stage is the exact bridge from torque surfaces into learner-visible attitude and rate outputs."
        },
        {
            14, "MissileGuidance", "OnUpdate", "combat", true, true,
            string_list({"Velocity", "Transform", "Missile", "GuidanceModelRef"}),
            string_list({"Velocity", "Missile"}),
            string_list({"truth.velocity", "packed.Missile", "apply_signatures"}),
            string_list({"RotationalIntegrate"}),
            "Update missile body velocity through the guidance model.",
            "This stage is inert for aircraft-only traces but remains in the first exact scope because mixed-world parity depends on the same ordered pipeline."
        },
        {
            15, "LeapfrogIntegrate", "OnUpdate", "physics", true, true,
            string_list({"Transform", "Velocity", "ForceAccumulator", "Mass"}),
            string_list({"Transform", "Velocity"}),
            string_list({"truth.position", "truth.velocity", "apply_signatures"}),
            string_list({"MissileGuidance"}),
            "Advance translation with the exact force-driven leapfrog integrator.",
            "This is the stage where accumulated linear forces become world-space position and velocity drift; later navigation and terminal surfaces depend on these exact results."
        },
        {
            16, "NavigationSystem", "OnUpdate", "navigation", true, true,
            string_list({"EGI", "Transform", "Velocity"}),
            string_list({"EGI"}),
            string_list({"hidden_dynamics.egi", "apply_signatures"}),
            string_list({"LeapfrogIntegrate"}),
            "Refresh deterministic EGI outputs from the integrated world pose and velocity.",
            "Instrument readout and exact packed hidden surfaces both depend on the post-integration EGI cache."
        },
        {
            19, "UpdateInstruments", "OnUpdate", "observation", true, true,
            string_list({
                "InstrumentState", "Transform", "Velocity", "AeroState", "ForceAccumulator",
                "Mass", "Propulsion", "AngularVelocity", "FuelSystem", "LandingGear",
                "PilotAction", "MissionCommandControlState", "MissionCommand", "RWR", "Ammo",
                "EGI", "EnvironmentModelRef"
            }),
            string_list({"InstrumentState"}),
            string_list({"instrument", "terminal"}),
            string_list({"NavigationSystem"}),
            "Build learner-facing instrument outputs from exact physics, navigation, and typed or mission command projections.",
            "Instrument consumers now read MissionCommand plus typed air-control overlays instead of treating MovementCommand as maintained truth. Legacy mirrors remain upstream compatibility evidence only."
        },
        {
            24, "FuelConsumption", "OnUpdate", "logistics", true, true,
            string_list({"FuelSystem", "Propulsion"}),
            string_list({"FuelSystem"}),
            string_list({"packed.FuelSystem", "apply_signatures"}),
            string_list({"UpdateInstruments"}),
            "Consume fuel from the resolved propulsion runtime state and update fuel-flow state.",
            "Propulsion runtime state is the maintained fuel-burn input here. Upstream throttle resolution may consult typed control-state or compatibility bridges, but this ledger must not restate command DTOs as live fuel-stage truth."
        },
        {
            25, "MassUpdate", "OnUpdate", "logistics", true, true,
            string_list({"MassProperties", "Mass", "FuelSystem"}),
            string_list({"MassProperties", "Mass"}),
            string_list({"packed.MassProperties", "packed.Mass", "apply_signatures"}),
            string_list({"FuelConsumption"}),
            "Recompute rigid-body and reference mass from the updated fuel system.",
            "This is the final traceable stage in the first scope because exact packed-state replay and later frames depend on mass being synchronized with fuel burn."
        },
    };
    return contracts;
}

const ExactStepStageDescriptor* find_exact_gpu_stage_descriptor(std::string_view stage_name) {
    const auto& inventory = exact_gpu_stage_inventory();
    auto it = std::find_if(
        inventory.begin(),
        inventory.end(),
        [&](const ExactStepStageDescriptor& descriptor) {
            return descriptor.name == stage_name;
        }
    );
    return it == inventory.end() ? nullptr : &(*it);
}

} // namespace

std::vector<ExactStepStageDescriptor> SimulationKernel::exact_gpu_migration_stage_inventory() const {
    return exact_gpu_stage_inventory();
}

std::vector<ExactStepStageContractDescriptor> SimulationKernel::exact_gpu_migration_stage_contract_inventory() const {
    return exact_gpu_stage_contract_inventory();
}

void SimulationKernel::begin_exact_stage_trace_frame() {
    if (exact_stage_trace_frame_active_) {
        throw std::logic_error("exact-stage trace frame already active");
    }
    ecs_frame_begin(ecs.c_ptr(), time_step);
    exact_stage_trace_frame_active_ = true;
}

void SimulationKernel::end_exact_stage_trace_frame() {
    if (!exact_stage_trace_frame_active_) {
        throw std::logic_error("exact-stage trace frame is not active");
    }
    ecs_frame_end(ecs.c_ptr());
    exact_stage_trace_frame_active_ = false;
}

bool SimulationKernel::run_exact_stage_trace_stage(const std::string& stage_name) {
    const auto* descriptor = find_exact_gpu_stage_descriptor(stage_name);
    if (descriptor == nullptr || !descriptor->manual_trace_supported) {
        return false;
    }
    if (!exact_stage_trace_frame_active_) {
        throw std::logic_error("run_exact_stage_trace_stage requires an active exact-stage trace frame");
    }
    const auto system = ecs.lookup(stage_name.c_str());
    if (!system.is_valid()) {
        throw std::runtime_error("exact-stage trace system lookup failed for stage: " + stage_name);
    }
    ecs_run(ecs.c_ptr(), system.id(), time_step, nullptr);
    return true;
}

bool SimulationKernel::run_exact_stage_direct(const std::string& stage_name) {
    if (exact_stage_trace_frame_active_) {
        throw std::logic_error("run_exact_stage_direct cannot execute while an exact-stage trace frame is active");
    }
    const auto system = ecs.lookup(stage_name.c_str());
    if (!system.is_valid()) {
        return false;
    }
    ecs_run(ecs.c_ptr(), system.id(), time_step, nullptr);
    return true;
}

void SimulationKernel::restore_exact_replay_world_time(double world_time_s) {
    if (exact_stage_trace_frame_active_) {
        throw std::logic_error("restore_exact_replay_world_time cannot run during an exact-stage trace frame");
    }
    ecs_reset_clock(ecs.c_ptr());
    if (world_time_s > 0.0) {
        ecs_frame_begin(ecs.c_ptr(), static_cast<ecs_ftime_t>(world_time_s));
        ecs_frame_end(ecs.c_ptr());
    }
}

void SimulationKernel::step_exact_stage_traceable_pipeline() {
    begin_exact_stage_trace_frame();
    try {
        for (const auto& descriptor : exact_gpu_stage_inventory()) {
            if (descriptor.gpu_migration_scope && descriptor.manual_trace_supported) {
                if (!run_exact_stage_trace_stage(descriptor.name)) {
                    throw std::runtime_error("failed to run exact-stage trace stage: " + descriptor.name);
                }
            }
        }
        end_exact_stage_trace_frame();
    } catch (...) {
        if (exact_stage_trace_frame_active_) {
            ecs_frame_end(ecs.c_ptr());
            exact_stage_trace_frame_active_ = false;
        }
        throw;
    }
}
