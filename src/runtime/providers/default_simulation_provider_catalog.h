#pragma once

#include "runtime/composition/composition_error.h"

#include <memory>
#include <cstdint>
#include <array>
#include <mutex>
#include <random>
#include <string>
#include <string_view>

namespace flecs {
class world;
}

class IAcousticModel;
class IControlModel;
class IEffectsModel;
class IEngagementEventStore;
class IEnvironmentModel;
class IGuidanceModel;
class ISensorModel;
class IUnitFactory;
class IWeaponReleaseService;
class SimulationKernel;
struct MissileTuning;

namespace runtime::providers {

class DefaultSimulationComposition {
  public:
    ~DefaultSimulationComposition();

    DefaultSimulationComposition(const DefaultSimulationComposition &) = delete;
    DefaultSimulationComposition &operator=(const DefaultSimulationComposition &) = delete;
    DefaultSimulationComposition(DefaultSimulationComposition &&) = delete;
    DefaultSimulationComposition &operator=(DefaultSimulationComposition &&) = delete;

    [[nodiscard]] std::string requested_manifest_sha256() const;
    [[nodiscard]] std::string resolved_manifest_sha256() const;
    [[nodiscard]] std::uint64_t world_generation() const noexcept;
    [[nodiscard]] std::array<std::uint64_t, 5> scope_generations() const noexcept;
    [[nodiscard]] composition::CompositionStatus rebuild_world(std::string_view barrier);
    void stop() noexcept;

  private:
    struct Impl;
    explicit DefaultSimulationComposition(std::unique_ptr<Impl> impl) noexcept;

    [[nodiscard]] IEnvironmentModel *environment_model() const noexcept;
    [[nodiscard]] IUnitFactory *unit_factory() const noexcept;
    [[nodiscard]] IEffectsModel *effects_model() const noexcept;
    [[nodiscard]] ISensorModel *sensor_model() const noexcept;
    [[nodiscard]] IAcousticModel *acoustic_model() const noexcept;
    [[nodiscard]] IControlModel *control_model() const noexcept;
    [[nodiscard]] IGuidanceModel *guidance_model() const noexcept;
    [[nodiscard]] IEngagementEventStore *engagement_event_store() const noexcept;
    [[nodiscard]] IWeaponReleaseService *weapon_release_service() const noexcept;

    friend class ::SimulationKernel;
    friend composition::CompositionResult<std::unique_ptr<DefaultSimulationComposition>>
    build_default_simulation_composition(SimulationKernel &kernel, flecs::world &world,
                                         MissileTuning &missile_tuning, std::mt19937 &rng,
                                         std::string_view resolved_manifest_json);
    friend composition::CompositionResult<std::unique_ptr<DefaultSimulationComposition>>
    build_default_simulation_composition_impl(SimulationKernel &kernel, flecs::world &world,
                                              MissileTuning &missile_tuning, std::mt19937 &rng,
                                              std::string_view resolved_manifest_json,
                                              std::string_view fail_effect_provider);

    std::unique_ptr<Impl> impl_;
};

using DefaultSimulationCompositionResult =
    composition::CompositionResult<std::unique_ptr<DefaultSimulationComposition>>;

// Materialize the repository-owned default compatibility artifact from the
// generated contract header. Default callers use these exact bytes; the
// production builder itself never interprets an empty manifest as fallback
// authority.
[[nodiscard]] std::string default_compatibility_resolved_manifest_json();

// Parse and bind an externally supplied resolved artifact to the exact native
// executable graph before SimulationKernel registers anything into Flecs.
[[nodiscard]] composition::CompositionStatus
validate_default_simulation_composition_manifest(std::string_view resolved_manifest_json);

[[nodiscard]] DefaultSimulationCompositionResult
build_default_simulation_composition(SimulationKernel &kernel, flecs::world &world,
                                     MissileTuning &missile_tuning, std::mt19937 &rng,
                                     std::string_view resolved_manifest_json);

} // namespace runtime::providers
