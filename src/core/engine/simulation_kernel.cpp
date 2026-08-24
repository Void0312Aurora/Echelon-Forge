#include "simulation_kernel.h"

#include "components/physics/instruments.h"
#include "core/interfaces/acoustic_model.h"
#include "core/interfaces/control_model.h"
#include "core/interfaces/effects_model.h"
#include "core/interfaces/engagement_event_store.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/guidance_model.h"
#include "core/interfaces/sensor_model.h"
#include "core/interfaces/unit_factory.h"
#include "runtime/providers/default_simulation_provider_catalog.h"

#include <spdlog/spdlog.h>

#include <cmath>
#include <stdexcept>
#include <string>

SimulationKernel::SimulationKernel()
    : SimulationKernel(runtime::providers::default_compatibility_resolved_manifest_json()) {}

SimulationKernel::SimulationKernel(std::string resolved_manifest_json) {
    const auto admission = runtime::providers::validate_default_simulation_composition_manifest(
        resolved_manifest_json);
    if (!admission) {
        const auto &error = admission.error();
        throw std::runtime_error("default simulation composition failed: " + error.code + ":" +
                                 error.subject + ":" + error.detail);
    }
    register_components_and_systems();
    auto composition = runtime::providers::build_default_simulation_composition(
        *this, ecs, missile_tuning_, rng, resolved_manifest_json);
    if (!composition) {
        const auto &error = composition.error();
        throw std::runtime_error("default simulation composition failed: " + error.code + ":" +
                                 error.subject + ":" + error.detail);
    }
    composition_ = std::move(composition).value();
    if (auto resupply_logic = ecs.lookup("ResupplyLogic"); resupply_logic.is_valid()) {
        ecs_enable(ecs.c_ptr(), resupply_logic.id(), false);
    }
    reset(42); // Default reset
    // Constructor initialization establishes generation 1's clean baseline;
    // later explicit resets are truth mutations and close the rebuild barrier.
    world_state_mutated_ = false;
}

SimulationKernel::~SimulationKernel() {
    shutdown();
}

void SimulationKernel::ensure_active(const char *operation) const {
    if (shutdown_complete_) {
        throw std::logic_error(std::string("SimulationKernel::") + operation +
                               " cannot be used after shutdown");
    }
}

void SimulationKernel::shutdown() {
    auto composition_lock = acquire_composition_operation();
    if (shutdown_complete_) {
        return;
    }
    shutdown_complete_ = true;

    if (exact_stage_trace_frame_active_) {
        ecs_frame_end(ecs.c_ptr());
        exact_stage_trace_frame_active_ = false;
    }

    ecs.delete_with<SimObject>();
    if (composition_) {
        composition_->stop();
        composition_.reset();
    }
    ecs.reset();
}

bool SimulationKernel::load_unit_definitions(const std::string &path, std::string *error) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("load_unit_definitions");
    world_state_mutated_ = true;
    IUnitFactory *factory = unit_factory();
    if (factory == nullptr) {
        if (error) *error = "Unit factory not set.";
        return false;
    }
    return factory->load_definitions(path, error);
}

void SimulationKernel::set_missile_tuning(const MissileTuning &tuning) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("set_missile_tuning");
    missile_tuning_ = tuning;
    world_state_mutated_ = true;
}

void SimulationKernel::reset(unsigned int seed) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("reset");
    if (IEngagementEventStore *store = engagement_event_store()) {
        store->clear();
    }

    // Delete all simulation entities (tagged with SimObject)
    // This is safer than delete_with<Transform> as it won't affect
    // potential non-simulation entities (e.g., UI, config singletons)
    ecs.delete_with<SimObject>();

    // Reset simulation time so resets are reproducible and episode-local.
    ecs_reset_clock(ecs.c_ptr());

    rng.seed(seed);
    world_state_mutated_ = true;

    spdlog::info("Simulation Reset with seed {}", seed);
}

void SimulationKernel::step() {
    auto composition_lock = acquire_composition_operation();
    ensure_active("step");
    if (exact_stage_trace_frame_active_) {
        throw std::logic_error(
            "SimulationKernel::step() cannot run while an exact-stage trace frame is active");
    }
    // Fixed timestep update
    // We pass the fixed delta_time to progress
    // This overrides the internal clock measuring
    world_state_mutated_ = true;
    ecs.progress(time_step);
}

bool SimulationKernel::load_database(const std::string &path) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("load_database");
    world_state_mutated_ = true;
    std::string error;
    IUnitFactory *factory = unit_factory();
    if (factory != nullptr && factory->load_definitions(path, &error)) {
        spdlog::info("Database loaded from: {}", path);
        return true;
    }
    spdlog::error("Failed to load database: {}", error);
    return false;
}

void SimulationKernel::set_time_step(double dt) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("set_time_step");
    if (!std::isfinite(dt) || dt <= 0.0) {
        throw std::invalid_argument(
            "SimulationKernel time step must be finite and greater than zero");
    }
    time_step = dt;
    world_state_mutated_ = true;
}

flecs::entity SimulationKernel::spawn_unit(Side side, const std::string &unit_name, double x,
                                           double y, double z, double heading, double pitch,
                                           double roll, double vx, double vy, double vz) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("spawn_unit");
    world_state_mutated_ = true;
    IUnitFactory *factory = unit_factory();
    if (factory == nullptr) {
        spdlog::error("Unit factory not set; cannot spawn unit.");
        return flecs::entity::null();
    }

    // Optional: Check existence first or trust spawn to handle it.
    // The factory->spawn is responsible for lookup now.
    SpawnParams params{side, x, y, z, heading, pitch, roll, vx, vy, vz};
    auto e = factory->spawn(ecs, unit_name, params);
    if (e.is_valid()) {
        e.add<SimObject>(); // Tag for cleanup
    }
    return e;
}

void SimulationKernel::clear_zones() {
    auto composition_lock = acquire_composition_operation();
    ensure_active("clear_zones");
    world_state_mutated_ = true;
    if (IEnvironmentModel *model = environment_model()) {
        model->clear_zones();
    }
}

void SimulationKernel::add_zone(const std::string &name, double x, double y, double width,
                                double height, double heading, int surface_type) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("add_zone");
    world_state_mutated_ = true;
    if (IEnvironmentModel *model = environment_model()) {
        model->add_zone(name, x, y, width, height, heading,
                        static_cast<IEnvironmentModel::SurfaceType>(surface_type));
    }
}

void SimulationKernel::set_wind(double speed_mps, double dir_from_deg, double shear_mps_per_km) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("set_wind");
    world_state_mutated_ = true;
    if (IEnvironmentModel *model = environment_model()) {
        model->set_wind(speed_mps, dir_from_deg, shear_mps_per_km);
    }
}

void SimulationKernel::set_sun_direction(double azimuth_deg, double elevation_deg) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("set_sun_direction");
    world_state_mutated_ = true;
    if (IEnvironmentModel *model = environment_model()) {
        model->set_sun_direction(azimuth_deg, elevation_deg);
    }
}

Vec3 SimulationKernel::get_sun_direction() const {
    auto composition_lock = acquire_composition_operation();
    ensure_active("get_sun_direction");
    if (IEnvironmentModel *model = environment_model()) {
        return model->get_sun_direction();
    }
    return {0.0, 0.7071, 0.7071};
}

void SimulationKernel::set_terrain_type(const std::string &terrain_type) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("set_terrain_type");
    world_state_mutated_ = true;
    if (IEnvironmentModel *model = environment_model()) {
        model->set_terrain_type(terrain_type);
    }
}

void SimulationKernel::set_maritime_state(double sea_state, double wave_heading_deg,
                                          double wave_period_s) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("set_maritime_state");
    world_state_mutated_ = true;
    if (IEnvironmentModel *model = environment_model()) {
        model->set_maritime_state(sea_state, wave_heading_deg, wave_period_s);
    }
}

void SimulationKernel::clear_maritime_state() {
    auto composition_lock = acquire_composition_operation();
    ensure_active("clear_maritime_state");
    world_state_mutated_ = true;
    if (IEnvironmentModel *model = environment_model()) {
        model->clear_maritime_state();
    }
}

IEnvironmentModel::MaritimeState SimulationKernel::get_maritime_state() const {
    auto composition_lock = acquire_composition_operation();
    ensure_active("get_maritime_state");
    if (IEnvironmentModel *model = environment_model()) {
        return model->get_maritime_state();
    }
    return {};
}

std::string SimulationKernel::requested_composition_sha256() const {
    auto composition_lock = acquire_composition_operation();
    return composition_ ? composition_->requested_manifest_sha256() : std::string{};
}

std::string SimulationKernel::resolved_composition_sha256() const {
    auto composition_lock = acquire_composition_operation();
    return composition_ ? composition_->resolved_manifest_sha256() : std::string{};
}

std::uint64_t SimulationKernel::world_composition_generation() const noexcept {
    auto composition_lock = acquire_composition_operation();
    return composition_ ? composition_->world_generation() : 0;
}

std::array<std::uint64_t, 5> SimulationKernel::composition_scope_generations() const noexcept {
    auto composition_lock = acquire_composition_operation();
    return composition_ ? composition_->scope_generations() : std::array<std::uint64_t, 5>{};
}

SimulationKernel::WorldLease SimulationKernel::acquire_world_lease() {
    auto composition_lock = acquire_composition_operation();
    ensure_active("acquire_world_lease");
    raw_world_access_exposed_ = true;
    return WorldLease(std::move(composition_lock), ecs);
}

SimulationKernel::ConstWorldLease SimulationKernel::acquire_world_lease() const {
    auto composition_lock = acquire_composition_operation();
    ensure_active("acquire_world_lease");
    raw_world_access_exposed_ = true;
    return ConstWorldLease(std::move(composition_lock), ecs);
}

double SimulationKernel::get_time_step() const {
    auto composition_lock = acquire_composition_operation();
    ensure_active("get_time_step");
    return time_step;
}

MissileTuning SimulationKernel::get_missile_tuning() const {
    auto composition_lock = acquire_composition_operation();
    ensure_active("get_missile_tuning");
    return missile_tuning_;
}

bool SimulationKernel::rebuild_world_composition(std::string_view barrier, std::string *error) {
    auto composition_lock = acquire_composition_operation();
    ensure_active("rebuild_world_composition");
    if (!composition_) {
        if (error) *error = "default simulation composition is unavailable";
        return false;
    }
    if (exact_stage_trace_frame_active_) {
        if (error) {
            *error = std::string(runtime::composition::kErrorRebuildBarrierRejected) +
                     ":world:exact-stage trace frame is active";
        }
        return false;
    }
    if (raw_world_access_exposed_) {
        if (error) {
            *error =
                std::string(runtime::composition::kErrorRebuildBarrierRejected) +
                ":world:raw Flecs world access has been exposed; rebuild requires a world lease";
        }
        return false;
    }
    if (ecs.count<SimObject>() != 0) {
        if (error) {
            *error = std::string(runtime::composition::kErrorRebuildBarrierRejected) +
                     ":world:non-quiescent world contains SimObject entities";
        }
        return false;
    }
    if (world_state_mutated_) {
        if (error) {
            *error = std::string(runtime::composition::kErrorRebuildBarrierRejected) +
                     ":world:world state has been mutated since composition construction";
        }
        return false;
    }
    auto status = composition_->rebuild_world(barrier);
    if (!status) {
        if (error) {
            const auto &failure = status.error();
            *error = failure.code + ":" + failure.subject + ":" + failure.detail;
        }
        return false;
    }
    return true;
}

IEnvironmentModel *SimulationKernel::environment_model() const noexcept {
    return composition_ ? composition_->environment_model() : nullptr;
}

IUnitFactory *SimulationKernel::unit_factory() const noexcept {
    return composition_ ? composition_->unit_factory() : nullptr;
}

IEffectsModel *SimulationKernel::effects_model() const noexcept {
    return composition_ ? composition_->effects_model() : nullptr;
}

ISensorModel *SimulationKernel::sensor_model() const noexcept {
    return composition_ ? composition_->sensor_model() : nullptr;
}

IAcousticModel *SimulationKernel::acoustic_model() const noexcept {
    return composition_ ? composition_->acoustic_model() : nullptr;
}

IControlModel *SimulationKernel::control_model() const noexcept {
    return composition_ ? composition_->control_model() : nullptr;
}

IGuidanceModel *SimulationKernel::guidance_model() const noexcept {
    return composition_ ? composition_->guidance_model() : nullptr;
}

IEngagementEventStore *SimulationKernel::engagement_event_store() const noexcept {
    return composition_ ? composition_->engagement_event_store() : nullptr;
}

IWeaponReleaseService *SimulationKernel::weapon_release_service() const noexcept {
    return composition_ ? composition_->weapon_release_service() : nullptr;
}
