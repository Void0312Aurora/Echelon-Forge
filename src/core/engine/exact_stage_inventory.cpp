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
         "Delivers pending movement commands into the live command surface.",
         true, true},
        {3, "CommandLinkAction", "OnUpdate", "command",
         "Delivers pending action commands into the live action surface.",
         true, true},
        {4, "CommandLinkMission", "OnUpdate", "command",
         "Delivers pending mission commands into the live mission surface.",
         true, true},
        {5, "ActionMapping", "OnUpdate", "command",
         "Maps normalized RL action inputs into movement-command targets.",
         true, true},
        {6, "CommandLag", "OnUpdate", "command",
         "Applies the exact command-lag filter to heading, speed, and altitude.",
         true, true},
        {7, "FlightControl", "OnUpdate", "control",
         "Runs the control model and refreshes filtered control-law state.",
         true, true},
        {8, "ClearForces", "OnLoad", "physics",
         "Clears ForceAccumulator before exact force/torque buildup.",
         true, true},
        {9, "ComputeAeroState", "OnUpdate", "physics",
         "Refreshes air-relative dynamic pressure, Mach, AoA, and beta.",
         true, true},
        {10, "ComputeForces", "OnUpdate", "physics",
         "Adds gravity and propulsion forces and updates propulsion readout.",
         true, true},
        {11, "ComputeAerodynamics", "OnUpdate", "physics",
         "Adds aerodynamic force and torque surfaces from aero state.",
         true, true},
        {12, "GroundContact", "OnUpdate", "physics",
         "Applies ground normal force, tire friction, and ground-restoring torques.",
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
         "Refreshes learner-facing instrument outputs from exact state.",
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
         "Consumes fuel and updates afterburner/fuel-flow state.",
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
    static const std::vector<ExactStepStageContractDescriptor> contracts = {
        {
            2, "CommandLinkMovement", "OnUpdate", "command", true, true,
            string_list({"PendingMovementCommand", "CommandLink", "world_time_total"}),
            string_list({"MovementCommand", "PendingMovementCommand.active"}),
            string_list({"packed.MovementCommand", "packed.PendingMovementCommand", "apply_signatures"}),
            string_list({}),
            "Deliver queued movement commands whose latency window has expired.",
            "Consumes the global frame clock. It is the first exact stage that mutates movement-command intent."
        },
        {
            3, "CommandLinkAction", "OnUpdate", "command", true, true,
            string_list({"PendingActionCommand", "CommandLink", "world_time_total"}),
            string_list({"ActionCommand", "PendingActionCommand.active"}),
            string_list({"packed.ActionCommand", "packed.PendingActionCommand", "apply_signatures"}),
            string_list({"CommandLinkMovement"}),
            "Deliver queued action commands into the live normalized action surface.",
            "Must run after movement delivery so both legacy and normalized command paths see the same frame time."
        },
        {
            4, "CommandLinkMission", "OnUpdate", "command", true, true,
            string_list({"PendingMissionCommand", "CommandLink", "world_time_total"}),
            string_list({"MissionCommand", "PendingMissionCommand.active"}),
            string_list({"packed.MissionCommand", "packed.PendingMissionCommand", "apply_signatures"}),
            string_list({"CommandLinkAction"}),
            "Deliver queued mission commands into the active mission surface.",
            "Mission routing and landing/recovery intent must be settled before action mapping and control-law logic."
        },
        {
            5, "ActionMapping", "OnUpdate", "command", true, true,
            string_list({"ActionCommand", "ActionSpaceConfig", "Transform", "Velocity", "MovementCommand"}),
            string_list({"MovementCommand"}),
            string_list({"packed.MovementCommand", "apply_signatures"}),
            string_list({"CommandLinkMission"}),
            "Map normalized RL actions onto legacy heading/speed/altitude targets.",
            "This is the bridge between learner actions and the exact movement-command lane; it seeds targets when no legacy command is active."
        },
        {
            6, "CommandLag", "OnUpdate", "command", true, true,
            string_list({"MovementCommand", "CommandLag", "Transform", "Velocity", "LaggedCommand"}),
            string_list({"LaggedCommand"}),
            string_list({"packed.LaggedCommand", "apply_signatures"}),
            string_list({"ActionMapping"}),
            "Apply first-order lag to heading, speed, and altitude targets.",
            "Control-law stages must consume lagged commands, not raw movement commands, to preserve exact actuator latency semantics."
        },
        {
            7, "FlightControl", "OnUpdate", "control", true, true,
            string_list({
                "LaggedCommand", "FlightModel", "PilotAction", "MissionCommand",
                "GroundState", "AeroState", "AngularVelocity", "ForceAccumulator",
                "ControlModelRef", "EnvironmentModelRef", "LandingGear"
            }),
            string_list({"ForceAccumulator", "ControlLawState", "LandingGear"}),
            string_list({
                "hidden_dynamics.force_accumulator",
                "hidden_dynamics.control_law_state",
                "packed.LandingGear",
                "apply_signatures"
            }),
            string_list({"CommandLag"}),
            "Run the exact control model, generate control torques, and update FBW filter state.",
            "Although the Flecs signature only exposes lagged command and flight model, the control model also reads PilotAction/MissionCommand/Aero/Ground state and mutates ForceAccumulator, ControlLawState, and gear transit state."
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
                "FlightModel", "MovementCommand", "PilotAction", "EnvironmentModelRef"
            }),
            string_list({"ForceAccumulator", "Propulsion"}),
            string_list({"hidden_dynamics.force_accumulator", "packed.Propulsion", "apply_signatures"}),
            string_list({"ComputeAeroState"}),
            "Accumulate gravity and thrust forces and cache propulsion state for later readout.",
            "Throttle source priority across PilotAction, MovementCommand, and ActionCommand must remain exact because later fuel and instrument stages depend on the chosen propulsion state."
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
                "LandingGear", "AngularVelocity", "ControlLawState", "PilotAction",
                "MovementCommand", "GearState", "Health", "EnvironmentModelRef"
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
            "Apply normal force, tire friction, steering, and ground-restoring torques.",
            "Ground-contact semantics span physics plus survivability state: it can damp velocity, mutate gear stress/collapse, and kill the entity through Health."
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
                "PilotAction", "MovementCommand", "MissionCommand", "RWR", "Ammo",
                "EGI", "EnvironmentModelRef"
            }),
            string_list({"InstrumentState"}),
            string_list({"instrument", "terminal"}),
            string_list({"NavigationSystem"}),
            "Build learner-facing instrument outputs from exact physics, navigation, and configuration state.",
            "This is the first stage whose primary outputs are the learner-visible instrument surface and terminal metadata derived from the current world state."
        },
        {
            24, "FuelConsumption", "OnUpdate", "logistics", true, true,
            string_list({"FuelSystem", "PilotAction", "MovementCommand", "ActionCommand"}),
            string_list({"FuelSystem"}),
            string_list({"packed.FuelSystem", "apply_signatures"}),
            string_list({"UpdateInstruments"}),
            "Consume fuel according to the resolved throttle source and update fuel-flow state.",
            "This stage runs after instrument refresh in the live CPU pipeline, so stage traces must treat FuelSystem as packed-state truth rather than expecting same-frame instrument fuel totals to update."
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
