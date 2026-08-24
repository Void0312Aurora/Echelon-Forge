#include "core/engine/testing/simulation_kernel_composition_test_access.h"

#include "core/engine/simulation_kernel.h"
#include "core/interfaces/acoustic_model.h"
#include "core/interfaces/control_model.h"
#include "core/interfaces/effects_model.h"
#include "core/interfaces/engagement_event_store.h"
#include "core/interfaces/environment_model.h"
#include "core/interfaces/guidance_model.h"
#include "core/interfaces/sensor_model.h"
#include "core/interfaces/weapon_release_service.h"
#include "runtime/providers/internal/default_simulation_provider_catalog_test_access.h"

SimulationKernelCompositionFailureProbeResult
SimulationKernelCompositionTestAccess::probe_default_provider_publication_failure_for_testing(
    SimulationKernel &kernel) {
    auto composition_lock = kernel.acquire_composition_operation();
    kernel.ensure_active("probe_default_provider_publication_failure_for_testing");

    const auto *effects_before = kernel.ecs.get<EffectsModelRef>();
    const auto *events_before = kernel.ecs.get<EngagementEventRecorderRef>();
    const auto *environment_before = kernel.ecs.get<EnvironmentModelRef>();
    const auto *acoustic_before = kernel.ecs.get<AcousticModelRef>();
    const auto *control_before = kernel.ecs.get<ControlModelRef>();
    const auto *guidance_before = kernel.ecs.get<GuidanceModelRef>();
    const auto *sensor_before = kernel.ecs.get<SensorModelRef>();
    const auto *weapon_release_before = kernel.ecs.get<WeaponReleaseServiceRef>();

    const auto effects_model_before = effects_before ? effects_before->model : nullptr;
    const auto event_recorder_before = events_before ? events_before->recorder : nullptr;
    const auto environment_model_before = environment_before ? environment_before->model : nullptr;
    const auto acoustic_model_before = acoustic_before ? acoustic_before->model : nullptr;
    const auto control_model_before = control_before ? control_before->model : nullptr;
    const auto guidance_model_before = guidance_before ? guidance_before->model : nullptr;
    const auto sensor_model_before = sensor_before ? sensor_before->model : nullptr;
    const auto weapon_release_service_before =
        weapon_release_before ? weapon_release_before->service : nullptr;

    auto result = runtime::providers::build_default_simulation_composition_for_testing(
        kernel, kernel.ecs, kernel.missile_tuning_, kernel.rng);

    const auto *effects_after = kernel.ecs.get<EffectsModelRef>();
    const auto *events_after = kernel.ecs.get<EngagementEventRecorderRef>();
    const auto *environment_after = kernel.ecs.get<EnvironmentModelRef>();
    const auto *acoustic_after = kernel.ecs.get<AcousticModelRef>();
    const auto *control_after = kernel.ecs.get<ControlModelRef>();
    const auto *guidance_after = kernel.ecs.get<GuidanceModelRef>();
    const auto *sensor_after = kernel.ecs.get<SensorModelRef>();
    const auto *weapon_release_after = kernel.ecs.get<WeaponReleaseServiceRef>();

    const bool singleton_references_restored =
        effects_after && effects_after->model == effects_model_before && events_after &&
        events_after->recorder == event_recorder_before && environment_after &&
        environment_after->model == environment_model_before && acoustic_after &&
        acoustic_after->model == acoustic_model_before && control_after &&
        control_after->model == control_model_before && guidance_after &&
        guidance_after->model == guidance_model_before && sensor_after &&
        sensor_after->model == sensor_model_before && weapon_release_after &&
        weapon_release_after->service == weapon_release_service_before;

    return {
        result ? std::string{} : result.error().code,
        singleton_references_restored,
    };
}
