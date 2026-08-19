cmake_minimum_required(VERSION 3.20)
project(EchelonForge VERSION 0.2.0 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
option(EF_ENABLE_CUDA_EXPERIMENTS "Enable experimental CUDA GPU helper surface (src/gpu/*.cu)" OFF)
# EF_ENABLE_CUDA_RESIDENT_BACKEND gates the cuda_resident world-step backend
# device sources independently of the GPU helper surface. The two surfaces have
# different semantic standing (optional accelerator helpers vs. a second
# world-step owner) and can be evaluated and enabled independently. Either flag
# being ON triggers enable_language(CUDA) and find_package(CUDAToolkit).
option(EF_ENABLE_CUDA_RESIDENT_BACKEND "Enable experimental CUDA-resident world-step backend" OFF)
option(EF_ENABLE_PROJECT_WARNINGS "Enable warning flags for maintained project targets" ON)

function(ef_enable_project_warnings target_name)
    if (NOT EF_ENABLE_PROJECT_WARNINGS)
        return()
    endif()
    target_compile_options(${target_name} PRIVATE
        $<$<COMPILE_LANG_AND_ID:C,GNU,Clang,AppleClang>:-Wall>
        $<$<COMPILE_LANG_AND_ID:C,GNU,Clang,AppleClang>:-Wextra>
        $<$<COMPILE_LANG_AND_ID:C,GNU,Clang,AppleClang>:-Wpedantic>
        $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-Wall>
        $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-Wextra>
        $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang,AppleClang>:-Wpedantic>
        $<$<COMPILE_LANG_AND_ID:C,MSVC>:/W4>
        $<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/W4>
    )
endfunction()

if (CMAKE_RANLIB)
    # Ensure static archives get a symbol index on all toolchains.
    set(CMAKE_C_ARCHIVE_FINISH "<CMAKE_RANLIB> <TARGET>")
    set(CMAKE_CXX_ARCHIVE_FINISH "<CMAKE_RANLIB> <TARGET>")
endif()

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(Threads REQUIRED)

include(FetchContent)

# 1. Flecs (ECS)
FetchContent_Declare(
    flecs
    GIT_REPOSITORY https://github.com/SanderMertens/flecs.git
    GIT_TAG        eeb9eaa64243536c5d5c19279c9c305a52d0b9b3 # v4.0.0
    SOURCE_SUBDIR  __cmo_no_upstream_cmake_project__
)
FetchContent_MakeAvailable(flecs)

# Flecs publishes SDK-oriented install rules (headers, archives, and CMake
# package metadata).  CMO only needs the runtime linked into its binaries, so
# build the upstream amalgamation as a private static dependency instead of
# adding the Flecs project to our install graph.  This keeps Python wheels
# self-contained without turning them into Flecs development SDKs.
add_library(ef_flecs STATIC "${flecs_SOURCE_DIR}/flecs.c")
target_include_directories(ef_flecs SYSTEM PUBLIC
    "${flecs_SOURCE_DIR}/include"
)
# The amalgamated flecs.c includes the upstream root flecs.h, which defines
# flecs_STATIC itself.  Consumers use include/flecs.h and need the definition
# propagated without redundantly defining it while compiling flecs.c.
target_compile_definitions(ef_flecs INTERFACE flecs_STATIC)
set_target_properties(ef_flecs PROPERTIES POSITION_INDEPENDENT_CODE ON)
if (WIN32)
    target_link_libraries(ef_flecs PUBLIC wsock32 ws2_32)
elseif (CMAKE_SYSTEM_NAME STREQUAL "Linux")
    target_link_libraries(ef_flecs PUBLIC Threads::Threads)
endif()
add_library(flecs::flecs ALIAS ef_flecs)

# 2. spdlog (Logging)
FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG        7c02e204c92545f869e2f04edaab1f19fe8b19fd # v1.13.0
)
FetchContent_MakeAvailable(spdlog)

# 3. nanobind (Python Bindings)
#
# The pinned v1.9.2 does not build with MinGW GCC on Windows: NB_EXPORT expands
# to __declspec(dllexport) (default visibility) while NB_NAMESPACE attaches
# visibility("hidden") for any __GNUC__ compiler, and GCC rejects the
# contradiction ("'dllexport' implies default visibility, but 'class
# nanobind::python_error' has already been declared with a different
# visibility").  Upstream fixed this in commit bcd9360, first released in
# v2.0.0, by restricting the hidden-visibility attribute to non-Windows GCC.
#
# Bumping to v2.0.0 is not currently viable: it changes the nb::shape and
# ndarray/lambda-signature APIs that src/interfaces/python uses.  Until those
# bindings are migrated, backport just the visibility guard.  The patch is a
# no-op on MSVC and Linux GCC, which already take the intended code path.
#
# UPDATE_DISCONNECTED caveat: on CMake < 3.27 a future GIT_TAG bump may leave
# an already-populated _deps/nanobind-src on the old revision, and the patch
# script would still apply cleanly against the stale source instead of failing
# closed.  Tag bumps therefore want a clean _deps (delete the nanobind-src /
# nanobind-subbuild dirs before reconfiguring).
FetchContent_Declare(
    nanobind
    GIT_REPOSITORY https://github.com/wjakob/nanobind.git
    GIT_TAG        80a30c8efb093b14f0e744bc7f6a9ef34beb3f7f # v1.9.2
    PATCH_COMMAND  "${CMAKE_COMMAND}"
                   "-DNANOBIND_DEFS_HEADER=<SOURCE_DIR>/include/nanobind/nb_defs.h"
                   -P "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patches/nanobind_mingw_visibility.cmake"
    UPDATE_DISCONNECTED TRUE
)
FetchContent_MakeAvailable(nanobind)

# 4. nlohmann_json (Config Loading)
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        9cca280a4d0ccf0c08f47a99aa71d1b0e52f8d03 # v3.11.3
)
FetchContent_MakeAvailable(nlohmann_json)

# --- Source Groups For Future Target Split ---
set(EF_CORE_ENGINE_SOURCES
    src/core/engine/simulation_kernel.cpp
    src/core/engine/simulation_kernel_engagement_event_store.cpp
    src/core/engine/simulation_kernel_services.cpp
    src/core/engine/simulation_kernel_weapon_release_service.cpp
    src/core/engine/simulation_kernel_command_surface.cpp
    src/core/engine/simulation_kernel_systems.cpp
    src/core/engine/simulation_kernel_command_api.cpp
    src/core/engine/simulation_kernel_observation_api.cpp
    src/core/engine/simulation_kernel_visual_api.cpp
    src/core/engine/simulation_kernel_weapon_api.cpp
    src/core/engine/simulation_kernel_damage_debug_api.cpp
    src/core/engine/exact_stage_inventory.cpp
    src/core/engine/world_batch_runtime.cpp
    src/runtime/providers/default_simulation_provider_catalog.cpp
)

# The default provider catalog embeds the generated resolved manifest. Keep an
# explicit dependency because localized MSVC /showIncludes output is not always
# consumed by every Ninja/CMake toolchain combination.
set_property(
    SOURCE src/runtime/providers/default_simulation_provider_catalog.cpp
    APPEND PROPERTY OBJECT_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/runtime/contracts/composition/default_compatibility_manifest.v1.generated.h"
)

set(EF_CORE_GEOMETRY_SOURCES
    src/core/geometry/spatial_query_runtime.cpp
)

set(EF_CORE_MISSION_RUNTIME_SOURCES
    src/core/mission/runtime/execution_observation_runtime.cpp
    src/core/mission/runtime/mission_runtime.cpp
    src/core/mission/runtime/execution_step_runtime.cpp
    src/core/mission/runtime/execution_episode_runtime.cpp
    src/core/mission/runtime/reward_runtime.cpp
    src/core/mission/runtime/objective_runtime.cpp
    src/core/mission/runtime/termination_runtime.cpp
)

set(EF_CORE_MISSION_EPISODE_SOURCES
    src/core/mission/episode/execution_episode_state.cpp
    src/core/mission/episode/execution_episode_batch_prepare.cpp
    src/core/mission/episode/execution_episode_controller.cpp
)

set(EF_CORE_MISSION_EPISODE_DETAIL_SOURCES
    src/core/mission/episode/detail/episode_transition_runtime.cpp
    src/core/mission/episode/detail/episode_reward_breakdown.cpp
    src/core/mission/episode/detail/mission_command_codec.cpp
)

set(EF_CORE_MISSION_SOURCES
    ${EF_CORE_MISSION_RUNTIME_SOURCES}
    ${EF_CORE_MISSION_EPISODE_SOURCES}
    ${EF_CORE_MISSION_EPISODE_DETAIL_SOURCES}
)

set(EF_RUNTIME_FACADE_SOURCES
    src/runtime/facade/internal/flecs_cpu_backend.cpp
    src/runtime/facade/runtime_facade.cpp
    src/runtime/facade/runtime_facade_config.cpp
    src/runtime/facade/runtime_facade_counterfactual.cpp
    src/runtime/facade/runtime_facade_world_setup.cpp
    src/runtime/facade/runtime_facade_query.cpp
    src/runtime/facade/runtime_facade_command_api.cpp
    src/runtime/facade/runtime_facade_execution.cpp
    src/runtime/facade/runtime_facade_packet.cpp
)

set(EF_MODEL_DEFAULT_SOURCES
    src/models/weapons/default_effects_model.cpp
    src/models/systems/default_sensor_model.cpp
    src/models/systems/default_acoustic_model.cpp
    src/models/environment/default_environment_model.cpp
    src/models/domains/air/default_control_model.cpp
    src/models/weapons/default_guidance_model.cpp
)

set(EF_CONTENT_SOURCES
    src/content/unit_definition_loader.cpp
    src/content/content_compile_passes.cpp
)

set(EF_COMPOSITION_SOURCES
    src/runtime/composition/composition_identity.cpp
    src/runtime/composition/composition_json.cpp
    src/runtime/composition/provider_catalog.cpp
    src/runtime/composition/composition_validation.cpp
    src/runtime/composition/composition_runtime.cpp
)

set(EF_CORE_SOURCES
    ${EF_CORE_ENGINE_SOURCES}
    ${EF_CORE_GEOMETRY_SOURCES}
    ${EF_CORE_MISSION_SOURCES}
    ${EF_MODEL_DEFAULT_SOURCES}
)

# --- Native Composition Lifecycle Library ---
# This target realizes the host-neutral composition contract without depending
# on ef_core, Flecs, a binding runtime, or Cordis. Keeping it as an independent
# link unit prevents lifecycle ownership from becoming another engine/facade
# compatibility path before the later provider-migration clusters are accepted.
add_library(ef_composition STATIC
    ${EF_COMPOSITION_SOURCES}
)
target_include_directories(ef_composition PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
target_link_libraries(ef_composition PRIVATE
    nlohmann_json::nlohmann_json
)

# --- Content Library (T3 first physical link-unit split, I46) ---
# content/ is the cleanest T3 leaf layer: its only maintained include edges are
# to the header-only components/ group plus its own content/ headers, and its sole
# translation unit (unit_definition_loader.cpp, ~1.9k lines) references no
# engine/mission/facade symbol.  Compiling it into its own static archive gives
# T3 a real, independently buildable/profilable link unit while keeping every
# consumer's include spelling ("content/...") unchanged -- ef_content re-exports
# the same src/ public include directory ef_core does, so no source file moves.
#
# The dependency is strictly one-way (ef_core -> ef_content): the loader calls
# only third-party json/spdlog plus its own header-only content headers, so
# there is no back-edge and therefore no MinGW single-pass link-order hazard.
# The third-party link set mirrors ef_core's so the TU compiles in a
# byte-identical environment to its previous in-ef_core compilation (flecs and
# Threads arrive transitively through the components/ headers content includes).
add_library(ef_content STATIC
    ${EF_CONTENT_SOURCES}
)

target_include_directories(ef_content PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(ef_content PUBLIC
    flecs::flecs
    spdlog::spdlog
    nlohmann_json::nlohmann_json
    Threads::Threads
)

# --- Core Library ---
add_library(ef_core STATIC
    ${EF_CORE_SOURCES}
)

target_include_directories(ef_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# The legacy core still uses the standard M_PI extension in several translation
# units. Opt in on MSVC so the real Flecs CPU backend can be built without
# changing the model formulas or their constants.
if (MSVC)
    target_compile_definitions(ef_core PRIVATE _USE_MATH_DEFINES)
endif()

# ef_content is listed first: ef_core's engine/model TUs call into the content
# loader (e.g. simulation_kernel.cpp -> default_unit_factory.h ->
# load_unit_definitions_json), and content never calls back, so ef_content must
# resolve after ef_core on a single-pass link line.  CMake derives that order
# from this dependency edge automatically for every downstream consumer.
target_link_libraries(ef_core PUBLIC
    ef_composition
    ef_content
    flecs::flecs
    spdlog::spdlog
    nlohmann_json::nlohmann_json
    Threads::Threads
)

# --- Facade Library (T3 second physical link-unit split, this iteration) ---
# runtime/facade is the T3 unit whose split direction is the *inverse* of the
# I46 content split: instead of a leaf below ef_core, the facade is the
# application layer strictly ABOVE it.  The governance gates already prove the
# direction is one-way -- nothing left inside ef_core (engine/geometry/mission/
# models) may #include runtime/facade (see
# test_facade_application_layer_has_no_incoming_edges_outside_its_permitted_callers),
# while facade TUs call down into engine/mission freely.  The remaining named
# T3 units (engine, mission) are NOT splittable yet: they are symbol-cyclic
# through the ratcheted world_batch_runtime.h -> execution_episode_controller.h
# edge (engine owns mission controllers by value), so cutting either one today
# would manufacture a static-library cycle; that stays deferred to the T4
# batch-wrapper design per the I41 allowlist verdicts.
#
# Because the facade sits on top, ef_core must NOT link ef_facade (that would
# declare a cycle); instead the two consumers whose TUs reference facade
# symbols (ef_py bindings and the ef_test facade suites) link ef_facade
# directly and receive ef_core transitively, which also guarantees the
# single-pass MinGW link order "consumer objects, ef_facade, ef_core, ..."
# that facade's undefined engine/mission symbols require.  No source file
# moves; every include spelling ("runtime/facade/...") is unchanged because
# ef_facade re-exports the same src/ public include directory ef_core does.
# The third-party link set mirrors ef_core's so each facade TU compiles in a
# byte-identical environment to its previous in-ef_core compilation.
add_library(ef_facade STATIC
    ${EF_RUNTIME_FACADE_SOURCES}
)

target_include_directories(ef_facade PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# ef_core is listed first: facade TUs resolve engine/mission/content symbols
# out of ef_core (and ef_content behind it), and nothing in ef_core calls back
# into the facade, so this is the one allowed direction.  CMake derives the
# "ef_facade before ef_core" final-link order from this edge automatically for
# every downstream consumer.
target_link_libraries(ef_facade PUBLIC
    ef_core
    flecs::flecs
    spdlog::spdlog
    nlohmann_json::nlohmann_json
    Threads::Threads
)

# --- Standalone App ---
# We keep src/main.cpp for local C++ testing, but now it needs to include/use SimulationKernel
# (main.cpp consumes SimulationKernel directly and references no facade symbol,
# so it keeps linking ef_core only.)
add_executable(ef_app src/main.cpp)
target_link_libraries(ef_app PRIVATE ef_core)

set(EF_PYTHON_BINDING_SOURCES
    src/interfaces/python/python_module.cpp
    src/interfaces/python/bindings_command.cpp
    src/interfaces/python/bindings_core.cpp
    src/interfaces/python/bindings_episode.cpp
    src/interfaces/python/bindings_runtime.cpp
    src/interfaces/python/bindings_gpu.cpp
)

# --- Python Module ---
nanobind_add_module(ef_py
    ${EF_PYTHON_BINDING_SOURCES}
)
# bindings_runtime.cpp/bindings_gpu.cpp reference RuntimeFacade symbols, so the
# bindings link the facade unit ahead of ef_core.  ef_core stays a *direct*
# link item on purpose: the engine's compatibility path calls gpu:: helpers
# (the ratcheted world_batch_runtime -> gpu edges) without a declared
# ef_core -> ef_gpu_experiments dependency, and it is ef_core's direct-item
# status that makes CMake repeat it after ef_gpu_experiments on the
# single-pass MinGW link line.  Dropping it in favour of the transitive edge
# through ef_facade could reorder that repetition away.
target_link_libraries(ef_py PRIVATE ef_facade ef_core)

# --- Experimental GPU Scaffolding ---
set(EF_GPU_MAINTAINED_HELPER_SOURCES
    src/gpu/gpu_visual_runtime.cpp
    src/gpu/gpu_execution_observation_runtime.cpp
    src/gpu/gpu_flight_shaping_runtime.cpp
    src/gpu/gpu_interaction_broadphase_runtime.cpp
)
set(EF_GPU_EXPERIMENT_SOURCES
    ${EF_GPU_MAINTAINED_HELPER_SOURCES}
)

if (EF_ENABLE_CUDA_EXPERIMENTS OR EF_ENABLE_CUDA_RESIDENT_BACKEND)
    enable_language(CUDA)
    find_package(CUDAToolkit REQUIRED)
endif()
if (EF_ENABLE_CUDA_EXPERIMENTS)
    list(APPEND EF_GPU_EXPERIMENT_SOURCES
        src/gpu/gpu_visual_runtime_cuda.cu
        src/gpu/gpu_execution_observation_runtime_cuda.cu
        src/gpu/gpu_flight_shaping_runtime_cuda.cu
        src/gpu/gpu_interaction_broadphase_runtime_cuda.cu
    )
endif()

# The resident backend is a separate experimental runtime target, not another
# Flecs/GPU-helper implementation. Its C++ lifecycle shell and CUDA-off stub
# are always compiled; only the instance-owned device metadata allocator is
# added when EF_ENABLE_CUDA_RESIDENT_BACKEND is explicitly enabled.
set(EF_CUDA_RESIDENT_BACKEND_SOURCES
    src/runtime/facade/internal/cuda_resident/cuda_resident_backend.cpp
    src/runtime/facade/internal/cuda_resident/cuda_resident_device_consumer.cpp
    src/runtime/facade/internal/cuda_resident/cuda_world_store.cpp
    src/runtime/facade/internal/cuda_resident/cuda_world_store_device_lease.cpp
)
if (EF_ENABLE_CUDA_RESIDENT_BACKEND)
    list(APPEND EF_CUDA_RESIDENT_BACKEND_SOURCES
        src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_storage.cu
        src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_barrier.cu
        src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_control_preparation.cu
        src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_observation.cu
        src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_state_readback.cu
        src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_window.cu
        src/runtime/facade/internal/cuda_resident/cuda_world_store_cuda_window_body.cu
    )
endif()

add_library(ef_cuda_resident_backend STATIC ${EF_CUDA_RESIDENT_BACKEND_SOURCES})
target_include_directories(ef_cuda_resident_backend PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
target_link_libraries(ef_cuda_resident_backend PUBLIC
    flecs::flecs
)
target_compile_definitions(ef_cuda_resident_backend PRIVATE
    $<$<BOOL:${EF_ENABLE_CUDA_RESIDENT_BACKEND}>:EF_ENABLE_CUDA_RESIDENT_BACKEND=1>
)
if (EF_ENABLE_CUDA_RESIDENT_BACKEND)
    target_link_libraries(ef_cuda_resident_backend PUBLIC CUDA::cudart)
    # `-maxrregcount=0` is an explicit no-cap declaration, not a tuning knob: it
    # is the value ptxas already uses by default. It is stated here because the
    # resource-evidence contract records `maxrregcount_argument` as provenance
    # and its collector requires the argument to be present and zero, so that a
    # future register-pressure experiment cannot be mistaken for the baseline.
    # Register counts are byte-identical with and without it.
    target_compile_options(ef_cuda_resident_backend PRIVATE
        $<$<COMPILE_LANGUAGE:CUDA>:--ptxas-options=-v>
        $<$<COMPILE_LANGUAGE:CUDA>:-maxrregcount=0>
    )
endif()

add_library(ef_cuda_resident_full_window_runner STATIC
    src/runtime/facade/internal/cuda_resident/cuda_resident_full_window_runner.cpp
    src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp
)
target_include_directories(ef_cuda_resident_full_window_runner PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
target_link_libraries(ef_cuda_resident_full_window_runner PUBLIC
    flecs::flecs
)

add_library(ef_gpu_experiments STATIC ${EF_GPU_EXPERIMENT_SOURCES})
target_include_directories(ef_gpu_experiments PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
target_link_libraries(ef_gpu_experiments PUBLIC
    ef_core
)
target_compile_definitions(ef_gpu_experiments PUBLIC
    $<$<BOOL:${EF_ENABLE_CUDA_EXPERIMENTS}>:EF_ENABLE_CUDA_EXPERIMENTS=1>
)

if (EF_ENABLE_CUDA_EXPERIMENTS)
    target_link_libraries(ef_gpu_experiments PUBLIC CUDA::cudart)
    set_target_properties(ef_gpu_experiments PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
    )
endif()

if (UNIX AND NOT APPLE)
    target_link_libraries(ef_py PRIVATE
        -Wl,--start-group
        ef_core
        ef_gpu_experiments
        -Wl,--end-group
    )
else()
    target_link_libraries(ef_py PRIVATE ef_gpu_experiments)
endif()

add_executable(ef_gpu_visual_phase0_probe
    src/tools/experimental/gpu_phase0/gpu_visual_phase0_probe.cpp
)
target_link_libraries(ef_gpu_visual_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_execution_observation_phase0_probe
    src/tools/experimental/gpu_phase0/gpu_execution_observation_phase0_probe.cpp
)
target_link_libraries(ef_gpu_execution_observation_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_flight_shaping_phase0_probe
    src/tools/experimental/gpu_phase0/gpu_flight_shaping_phase0_probe.cpp
)
target_link_libraries(ef_gpu_flight_shaping_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_interaction_broadphase_phase0_probe
    src/tools/experimental/gpu_phase0/gpu_interaction_broadphase_phase0_probe.cpp
)
target_link_libraries(ef_gpu_interaction_broadphase_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_sensor_candidate_phase0_probe
    src/tools/experimental/gpu_phase0/gpu_sensor_candidate_phase0_probe.cpp
)
target_link_libraries(ef_gpu_sensor_candidate_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_comm_candidate_phase0_probe
    src/tools/experimental/gpu_phase0/gpu_comm_candidate_phase0_probe.cpp
)
target_link_libraries(ef_gpu_comm_candidate_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_visual_candidate_phase0_probe
    src/tools/experimental/gpu_phase0/gpu_visual_candidate_phase0_probe.cpp
)
target_link_libraries(ef_gpu_visual_candidate_phase0_probe PRIVATE
    ef_gpu_experiments
)

# --- Testing ---
# 5. doctest (C++ unit test framework)
include(CTest)
if (BUILD_TESTING)
FetchContent_Declare(
    doctest
    GIT_REPOSITORY https://github.com/doctest/doctest.git
    GIT_TAG        ae7a13539fb71f270b87eb2e874fbac80bc8dda2 # v2.4.11
)
FetchContent_MakeAvailable(doctest)

set(EF_TEST_SOURCES
    src/tests/test_main.cpp
    src/tests/test_simulation_kernel_smoke.cpp
    src/tests/test_components_basic.cpp
    src/tests/test_content_compile_passes.cpp
    src/tests/test_aero_physics_common.cpp
    src/tests/test_kalman_seeker.cpp
    src/tests/test_structural_failure_system.cpp
    src/tests/test_control_surface_damage_coupling.cpp
    src/tests/test_world_batch_backend_contract.cpp
    src/tests/test_cuda_resident_backend_admission.cpp
    src/tests/test_cuda_resident_backend_lifecycle.cpp
    src/tests/test_cuda_resident_backend_state.cpp
    src/tests/test_cuda_resident_fixed_air_cpu_reference.cpp
    src/tests/test_cuda_resident_control_preparation_cpu_reference.cpp
    src/tests/test_cuda_resident_flight_dynamics_cpu_reference.cpp
    src/tests/test_cuda_resident_observation_projection_cpu_reference.cpp
    src/tests/test_cuda_resident_device_consumer.cpp
    src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp
    src/tests/test_cuda_resident_replay.cpp
    src/tests/test_cuda_resident_replay_projection.cpp
    src/tests/test_cuda_resident_replay_support.cpp
    src/tests/test_cuda_resident_performance.cpp
    src/tests/test_world_batch_runtime.cpp
    src/tests/test_runtime_facade_evidence_allocators.cpp
    src/tests/test_runtime_facade_maintained_replay_envelope.cpp
    src/tests/test_default_effects_model.cpp
)

add_executable(ef_test ${EF_TEST_SOURCES})
# test_runtime_facade_*.cpp reference RuntimeFacade symbols, so ef_test links
# ef_facade ahead of ef_core; the remaining suites keep their direct ef_core /
# ef_gpu_experiments edges unchanged.
target_link_libraries(ef_test PRIVATE
    ef_facade
    ef_core
    ef_cuda_resident_backend
    ef_gpu_experiments
    doctest::doctest
)
target_include_directories(ef_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)
if (MSVC)
    target_compile_definitions(ef_test PRIVATE _USE_MATH_DEFINES)
endif()

# P2-A is intentionally a focused native target. It links only the isolated
# lifecycle library and doctest, so passing this target cannot be mistaken for
# constructor, system, backend, binding, or Cordis integration.
add_executable(ef_composition_lifecycle_test
    src/tests/test_main.cpp
    src/tests/test_composition_lifecycle.cpp
)
target_link_libraries(ef_composition_lifecycle_test PRIVATE
    ef_composition
    doctest::doctest
    Threads::Threads
)
target_include_directories(ef_composition_lifecycle_test PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
target_compile_definitions(ef_composition_lifecycle_test PRIVATE
    EF_SOURCE_ROOT="${CMAKE_CURRENT_SOURCE_DIR}"
)

# Focused target for CUDA-on resident-backend validation. It deliberately avoids
# the full ef_core graph, whose current MSVC portability debt is unrelated to the
# RB3-RB7 lifecycle, state-barrier, Phase A/B, Phase-D, and device-view contracts.
add_executable(ef_cuda_resident_lifecycle_test
    src/tests/test_main.cpp
    src/tests/test_cuda_resident_backend_lifecycle.cpp
    src/tests/test_cuda_resident_backend_state.cpp
    src/tests/test_cuda_resident_control_preparation.cpp
    src/tests/test_cuda_resident_flight_dynamics.cpp
    src/tests/test_cuda_resident_observation_projection.cpp
    src/tests/test_cuda_resident_observation_projection_cpu_reference.cpp
    src/tests/test_cuda_resident_performance.cpp
    src/tests/test_cuda_resident_device_consumer.cpp
)
target_link_libraries(ef_cuda_resident_lifecycle_test PRIVATE
    ef_cuda_resident_backend
    doctest::doctest
)
target_include_directories(ef_cuda_resident_lifecycle_test PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# RB8 replay/shadow validation keeps the CUDA-on target independent of ef_core's
# pre-existing MSVC portability debt. Its CPU lane is the separately pinned
# fixed-air fixture oracle used by the CUDA CPU-reference tests, not a second
# maintained backend. Shadow results never route into RuntimeFacade or state.
add_executable(ef_cuda_resident_replay_test
    src/tests/test_main.cpp
    src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp
    src/tests/test_cuda_resident_replay.cpp
    src/tests/test_cuda_resident_replay_projection.cpp
    src/tests/test_cuda_resident_replay_support.cpp
)
target_link_libraries(ef_cuda_resident_replay_test PRIVATE
    ef_cuda_resident_backend
    doctest::doctest
)
target_include_directories(ef_cuda_resident_replay_test PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

add_executable(ef_cuda_resident_full_window_test
    src/tests/test_main.cpp
    src/tests/test_cuda_resident_full_window.cpp
)
target_link_libraries(ef_cuda_resident_full_window_test PRIVATE
    ef_cuda_resident_backend
    ef_cuda_resident_full_window_runner
    doctest::doctest
)
target_include_directories(ef_cuda_resident_full_window_test PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# CR2-2b compiles one probe source twice so the real Flecs CPU adapter and the
# CUDA-resident backend consume the same owned trace through the same Runner.
# CPU database loading remains outside the runner's semantic window surface.
if (EF_ENABLE_CUDA_RESIDENT_BACKEND)
    add_executable(ef_cuda_resident_full_window_cuda_probe
        src/tools/experimental/cuda_resident/cuda_resident_full_window_probe.cpp
    )
    target_link_libraries(ef_cuda_resident_full_window_cuda_probe PRIVATE
        ef_cuda_resident_backend
        ef_cuda_resident_full_window_runner
        nlohmann_json::nlohmann_json
    )
    target_compile_definitions(ef_cuda_resident_full_window_cuda_probe PRIVATE
        EF_CR2_FULL_WINDOW_CUDA_PROBE=1
    )
    target_include_directories(ef_cuda_resident_full_window_cuda_probe PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )

    # CR2-6 compiles the production matrix probe separately for the current
    # CUDA-resident lane. Both lanes use the same backend SPI window sequence;
    # the device-consumer suffix remains an explicit CUDA-only mode.
    add_executable(ef_cuda_resident_cr2_matrix_cuda_probe
        src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_probe.cpp
        src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_session.cpp
        src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp
    )
    target_link_libraries(ef_cuda_resident_cr2_matrix_cuda_probe PRIVATE
        ef_cuda_resident_backend
        nlohmann_json::nlohmann_json
    )
    target_compile_definitions(ef_cuda_resident_cr2_matrix_cuda_probe PRIVATE
        EF_CR2_MATRIX_CUDA_PROBE=1
        EF_CR2_MATRIX_BUILD_CONFIG="$<CONFIG>"
    )
    target_include_directories(ef_cuda_resident_cr2_matrix_cuda_probe PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )
else()
    add_executable(ef_cuda_resident_full_window_cpu_probe
        src/tools/experimental/cuda_resident/cuda_resident_full_window_probe.cpp
    )
    target_link_libraries(ef_cuda_resident_full_window_cpu_probe PRIVATE
        ef_facade
        ef_core
        ef_gpu_experiments
        ef_cuda_resident_full_window_runner
        nlohmann_json::nlohmann_json
    )
    target_compile_definitions(ef_cuda_resident_full_window_cpu_probe PRIVATE
        EF_CR2_FULL_WINDOW_CPU_PROBE=1
    )
    target_include_directories(ef_cuda_resident_full_window_cpu_probe PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )

    add_executable(ef_cuda_resident_cr2_matrix_cpu_probe
        src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_probe.cpp
        src/tools/experimental/cuda_resident/cuda_resident_cr2_matrix_session.cpp
        src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp
    )
    target_link_libraries(ef_cuda_resident_cr2_matrix_cpu_probe PRIVATE
        ef_facade
        ef_core
        ef_gpu_experiments
        nlohmann_json::nlohmann_json
    )
    target_compile_definitions(ef_cuda_resident_cr2_matrix_cpu_probe PRIVATE
        EF_CR2_MATRIX_CPU_PROBE=1
        EF_CR2_MATRIX_BUILD_CONFIG="$<CONFIG>"
    )
    target_include_directories(ef_cuda_resident_cr2_matrix_cpu_probe PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )
endif()

# RB9 measures the same frozen trace through two separately built Release
# probes. The CUDA-on probe keeps the existing ef_core/MSVC debt out of its
# graph; the CUDA-off probe uses the real FlecsCpuBackend instead of the RB8
# fixture oracle. Neither target is a maintained backend or admission surface.
if (EF_ENABLE_CUDA_RESIDENT_BACKEND)
    add_executable(ef_cuda_resident_rb9_cuda_probe
        src/tools/experimental/cuda_resident/cuda_resident_rb9_probe.cpp
        src/tools/experimental/cuda_resident/cuda_resident_rb9_probe_session.cpp
        src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp
    )
    target_link_libraries(ef_cuda_resident_rb9_cuda_probe PRIVATE
        ef_cuda_resident_backend
        nlohmann_json::nlohmann_json
    )
    target_compile_definitions(ef_cuda_resident_rb9_cuda_probe PRIVATE
        EF_RB9_CUDA_PROBE=1
        EF_RB9_BUILD_CONFIG="$<CONFIG>"
    )
    target_include_directories(ef_cuda_resident_rb9_cuda_probe PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )

    # CP-4 restored the capture entry point against a versioned kernel catalog
    # (kKernelSpecsV2 with a static-asserted 1:1 migration from frozen v1);
    # CP-5 moved it to v3 (kKernelSpecsV3 with a static-asserted fold from
    # frozen v2) after fusing the window graph. Backend and profiler
    # dependencies stay restored here. v1/v2 identifiers stay frozen and
    # kCaptureProbeV1Retired stays true; each generation supersedes the
    # previous rather than reviving it.
    add_executable(ef_cuda_resident_resource_probe
        src/tools/experimental/cuda_resident/cuda_resident_resource_probe.cpp
        src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp
    )
    target_link_libraries(ef_cuda_resident_resource_probe PRIVATE
        ef_cuda_resident_backend
        nlohmann_json::nlohmann_json
        CUDA::cudart
    )
    target_compile_definitions(ef_cuda_resident_resource_probe PRIVATE
        EF_RESOURCE_CAPTURE_BUILD_CONFIG="$<CONFIG>"
    )
    target_include_directories(ef_cuda_resident_resource_probe PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )
else()
    add_executable(ef_cuda_resident_rb9_cpu_probe
        src/tools/experimental/cuda_resident/cuda_resident_rb9_probe.cpp
        src/tools/experimental/cuda_resident/cuda_resident_rb9_probe_session.cpp
        src/runtime/facade/internal/cuda_resident/cuda_resident_replay_harness.cpp
    )
    target_link_libraries(ef_cuda_resident_rb9_cpu_probe PRIVATE
        ef_facade
        ef_core
        ef_gpu_experiments
        nlohmann_json::nlohmann_json
    )
    target_compile_definitions(ef_cuda_resident_rb9_cpu_probe PRIVATE
        EF_RB9_CPU_PROBE=1
        EF_RB9_BUILD_CONFIG="$<CONFIG>"
    )
    target_include_directories(ef_cuda_resident_rb9_cpu_probe PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )
endif()

# CTest entries for all doctest suites plus focused structural-failure lanes.
add_test(NAME ef_test_all COMMAND ef_test)
set_tests_properties(ef_test_all PROPERTIES WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}")
add_test(NAME structural_failure_state COMMAND ef_test --test-suite=structural_failure_state)
add_test(NAME structural_failure_events COMMAND ef_test --test-suite=structural_failure_events)
add_test(NAME structural_failure_break_modes COMMAND ef_test --test-suite=structural_failure_break_modes)
add_test(NAME structural_consequence COMMAND ef_test --test-suite=structural_consequence)
add_test(NAME aircraft_damage_lifecycle COMMAND ef_test --test-suite=aircraft_damage_lifecycle)
add_test(NAME world_batch_runtime COMMAND ef_test --test-suite=world_batch_runtime)
add_test(NAME cuda_resident_lifecycle COMMAND ef_cuda_resident_lifecycle_test)
add_test(NAME cuda_resident_replay COMMAND ef_cuda_resident_replay_test)
add_test(NAME cuda_resident_full_window COMMAND ef_cuda_resident_full_window_test)
add_test(NAME default_effects_model COMMAND ef_test --test-suite=default_effects_model)
set_tests_properties(default_effects_model PROPERTIES WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}")
add_test(NAME composition_lifecycle COMMAND ef_composition_lifecycle_test)
endif()

set(EF_PROJECT_WARNING_TARGETS
    ef_composition
    ef_core
    ef_content
    ef_facade
    ef_app
    ef_py
    ef_cuda_resident_backend
    ef_cuda_resident_full_window_runner
    ef_gpu_experiments
    ef_gpu_visual_phase0_probe
    ef_gpu_execution_observation_phase0_probe
    ef_gpu_flight_shaping_phase0_probe
    ef_gpu_interaction_broadphase_phase0_probe
    ef_gpu_sensor_candidate_phase0_probe
    ef_gpu_comm_candidate_phase0_probe
    ef_gpu_visual_candidate_phase0_probe
    ef_test
    ef_composition_lifecycle_test
    ef_cuda_resident_lifecycle_test
    ef_cuda_resident_replay_test
    ef_cuda_resident_full_window_test
    ef_cuda_resident_full_window_cpu_probe
    ef_cuda_resident_full_window_cuda_probe
    ef_cuda_resident_cr2_matrix_cpu_probe
    ef_cuda_resident_cr2_matrix_cuda_probe
    ef_cuda_resident_rb9_cpu_probe
    ef_cuda_resident_rb9_cuda_probe
    ef_cuda_resident_resource_probe
)

foreach(target_name IN LISTS EF_PROJECT_WARNING_TARGETS)
    if (TARGET ${target_name})
        ef_enable_project_warnings(${target_name})
    endif()
endforeach()

# Install the extension module
install(TARGETS ef_py DESTINATION .)
set_target_properties(ef_py PROPERTIES INSTALL_RPATH "$ORIGIN/lib")

# Keep runtime-relative resource lookup working in installed wheels.  The
# Python runtime resolves these paths from the wheel root, matching the source
# checkout layout.
install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/examples/config" DESTINATION examples)
install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/examples/__init__.py" DESTINATION examples)
install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/examples/agents" DESTINATION examples
    PATTERN "__pycache__" EXCLUDE
    PATTERN "*.pyc" EXCLUDE
)
install(DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/scenarios" DESTINATION .)
