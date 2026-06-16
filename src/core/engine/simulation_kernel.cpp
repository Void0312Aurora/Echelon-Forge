#include "simulation_kernel.h"
#include "simulation_kernel_engagement_event_store.h"
#include "simulation_kernel_services.h"

#include "components/physics/instruments.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/control_model.h"
#include "core/interfaces/acoustic_model.h"
#include "core/interfaces/effects_model.h"
#include "core/interfaces/guidance_model.h"
#include "core/interfaces/sensor_model.h"
#include "core/interfaces/unit_factory.h"
#include "core/interfaces/weapon_release_damage_bridge.h"
#include "models/core/default_unit_factory.h"

#include <spdlog/spdlog.h>

#include <cstdint>
#include <stdexcept>
#include <utility>

namespace {

class SimulationKernelWeaponReleaseDamageBridge final : public IWeaponReleaseDamageBridge {
  public:
    explicit SimulationKernelWeaponReleaseDamageBridge(SimulationKernel &kernel)
        : kernel_(kernel) {}

    bool apply_proximity_hit(std::uint64_t attacker_id, std::uint64_t target_id, double damage,
                             double fuse_distance) override {
        return kernel_.debug_apply_proximity_hit(attacker_id, target_id, damage, fuse_distance);
    }

  private:
    SimulationKernel &kernel_;
};

} // namespace

SimulationKernel::SimulationKernel()
    : environment_model_(make_default_environment_model()),
      unit_factory_(std::make_unique<DefaultUnitFactory>()),
      effects_model_(make_default_effects_model()), sensor_model_(make_default_sensor_model()),
      acoustic_model_(make_default_acoustic_model()), control_model_(make_default_control_model()),
      guidance_model_(make_default_guidance_model()),
      engagement_event_store_(std::make_unique<SimulationKernelEngagementEventStore>(ecs)),
      weapon_release_damage_bridge_(
          std::make_unique<SimulationKernelWeaponReleaseDamageBridge>(*this)),
      weapon_release_service_(make_simulation_kernel_weapon_release_service(
          ecs, unit_factory_, missile_tuning_, rng, *engagement_event_store_,
          *engagement_event_store_, *weapon_release_damage_bridge_)) {
    register_components_and_systems();
    if (auto resupply_logic = ecs.lookup("ResupplyLogic"); resupply_logic.is_valid()) {
        ecs_enable(ecs.c_ptr(), resupply_logic.id(), false);
    }
    reset(42); // Default reset
}

SimulationKernel::~SimulationKernel() {
    shutdown();
}

void SimulationKernel::shutdown() {
    if (shutdown_complete_) {
        return;
    }
    shutdown_complete_ = true;

    if (exact_stage_trace_frame_active_) {
        ecs_frame_end(ecs.c_ptr());
        exact_stage_trace_frame_active_ = false;
    }

    ecs.delete_with<SimObject>();
    ecs.reset();

    environment_model_.reset();
    unit_factory_.reset();
    effects_model_.reset();
    sensor_model_.reset();
    control_model_.reset();
    guidance_model_.reset();
}

void SimulationKernel::set_unit_factory(std::unique_ptr<IUnitFactory> factory) {
    if (factory) {
        unit_factory_ = std::move(factory);
    } else {
        spdlog::warn("Attempted to set a null unit factory; keeping current factory.");
    }
}

void SimulationKernel::set_effects_model(std::unique_ptr<IEffectsModel> model) {
    if (model) {
        effects_model_ = std::move(model);
        ecs.set<EffectsModelRef>({effects_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null effects model; keeping current model.");
    }
}

void SimulationKernel::set_sensor_model(std::unique_ptr<ISensorModel> model) {
    if (model) {
        sensor_model_ = std::move(model);
        ecs.set<SensorModelRef>({sensor_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null sensor model; keeping current model.");
    }
}

void SimulationKernel::set_acoustic_model(std::unique_ptr<IAcousticModel> model) {
    if (model) {
        acoustic_model_ = std::move(model);
        ecs.set<AcousticModelRef>({acoustic_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null acoustic model; keeping current model.");
    }
}

void SimulationKernel::set_control_model(std::unique_ptr<IControlModel> model) {
    if (model) {
        control_model_ = std::move(model);
        ecs.set<ControlModelRef>({control_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null control model; keeping current model.");
    }
}

void SimulationKernel::set_guidance_model(std::unique_ptr<IGuidanceModel> model) {
    if (model) {
        guidance_model_ = std::move(model);
        ecs.set<GuidanceModelRef>({guidance_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null guidance model; keeping current model.");
    }
}

void SimulationKernel::set_environment_model(std::unique_ptr<IEnvironmentModel> model) {
    if (model) {
        environment_model_ = std::move(model);
        ecs.set<EnvironmentModelRef>({environment_model_.get()});
    } else {
        spdlog::warn("Attempted to set a null environment model; keeping current model.");
    }
}

bool SimulationKernel::load_unit_definitions(const std::string &path, std::string *error) {
    if (!unit_factory_) {
        if (error) *error = "Unit factory not set.";
        return false;
    }
    return unit_factory_->load_definitions(path, error);
}

void SimulationKernel::set_missile_tuning(const MissileTuning &tuning) {
    missile_tuning_ = tuning;
}

void SimulationKernel::reset(unsigned int seed) {
    engagement_event_store_->clear();

    // Delete all simulation entities (tagged with SimObject)
    // This is safer than delete_with<Transform> as it won't affect
    // potential non-simulation entities (e.g., UI, config singletons)
    ecs.delete_with<SimObject>();

    // Reset simulation time so resets are reproducible and episode-local.
    ecs_reset_clock(ecs.c_ptr());

    rng.seed(seed);

    spdlog::info("Simulation Reset with seed {}", seed);
}

void SimulationKernel::step() {
    if (exact_stage_trace_frame_active_) {
        throw std::logic_error(
            "SimulationKernel::step() cannot run while an exact-stage trace frame is active");
    }
    // Fixed timestep update
    // We pass the fixed delta_time to progress
    // This overrides the internal clock measuring
    ecs.progress(time_step);
}

bool SimulationKernel::load_database(const std::string &path) {
    std::string error;
    if (unit_factory_->load_definitions(path, &error)) {
        spdlog::info("Database loaded from: {}", path);
        return true;
    }
    spdlog::error("Failed to load database: {}", error);
    return false;
}

flecs::entity SimulationKernel::spawn_unit(Side side, const std::string &unit_name, double x,
                                           double y, double z, double heading, double pitch,
                                           double roll, double vx, double vy, double vz) {
    if (!unit_factory_) {
        spdlog::error("Unit factory not set; cannot spawn unit.");
        return flecs::entity::null();
    }

    // Optional: Check existence first or trust spawn to handle it.
    // The factory->spawn is responsible for lookup now.
    SpawnParams params{side, x, y, z, heading, pitch, roll, vx, vy, vz};
    auto e = unit_factory_->spawn(ecs, unit_name, params);
    if (e.is_valid()) {
        e.add<SimObject>(); // Tag for cleanup
    }
    return e;
}

void SimulationKernel::clear_zones() {
    if (environment_model_) {
        environment_model_->clear_zones();
    }
}

void SimulationKernel::add_zone(const std::string &name, double x, double y, double width,
                                double height, double heading, int surface_type) {
    if (environment_model_) {
        environment_model_->add_zone(name, x, y, width, height, heading,
                                     (IEnvironmentModel::SurfaceType)surface_type);
    }
}

void SimulationKernel::set_wind(double speed_mps, double dir_from_deg, double shear_mps_per_km) {
    if (environment_model_) {
        environment_model_->set_wind(speed_mps, dir_from_deg, shear_mps_per_km);
    }
}

void SimulationKernel::set_terrain_type(const std::string &terrain_type) {
    if (environment_model_) {
        environment_model_->set_terrain_type(terrain_type);
    }
}

void SimulationKernel::set_maritime_state(double sea_state, double wave_heading_deg,
                                          double wave_period_s) {
    if (environment_model_) {
        environment_model_->set_maritime_state(sea_state, wave_heading_deg, wave_period_s);
    }
}

void SimulationKernel::clear_maritime_state() {
    if (environment_model_) {
        environment_model_->clear_maritime_state();
    }
}

IEnvironmentModel::MaritimeState SimulationKernel::get_maritime_state() const {
    if (environment_model_) {
        return environment_model_->get_maritime_state();
    }
    return {};
}
