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
option(EF_ENABLE_COMPILER_CACHE "Route C/C++ compiles through a compiler cache (sccache/ccache) when one is installed" OFF)
option(EF_FETCHCONTENT_REVALIDATE_PINS "Re-run the git update/patch steps of the pinned FetchContent dependencies on every configure" ON)

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

# --- Compiler Cache -------------------------------------------------------
# A compiler cache is a pass-through wrapper: CMake prefixes every compile
# command with it (the LAUNCHER slot the generators already emit), the wrapper
# hashes the preprocessed translation unit together with the argument vector,
# and on a miss it execs the identical compiler command line.  Flags, defines,
# include paths and the emitted object are therefore unchanged; only the wall
# time of a repeated compile changes.
#
# Measured on this repository's Windows toolchain (sccache 0.17.0, MSVC 14.44,
# Ninja, Release) the full ef_py command shape
#     /bigobj /MP /Os /showIncludes /Fo<obj> /Fd<pdb> /FS
# reports zero "Non-cacheable compilations" and zero "Unsupported compiler
# calls".  Two details matter for MSVC correctness and both were verified:
#   * /MP, which nanobind_add_module forces onto ef_py, is normalised away.  It
#     cannot change codegen for the one-translation-unit-per-invocation command
#     lines Ninja generates, so a /MP compile hits the same entry as the /MP-less
#     one instead of being rejected.
#   * The /showIncludes stream is NOT replayed verbatim, and on a toolchain
#     whose diagnostics are not ASCII that costs Ninja its header dependencies.
#     Measured here (MSVC 14.44 with only 2052\clui.dll installed, so cl emits
#     GBK and VSLANG cannot force English): cl writes the prefix as the bytes
#     D7 A2 D2 E2 3A 20 B0 FC BA AC CE C4 BC FE, which is exactly what CMake
#     detects and writes into rules.ninja, but sccache hands Ninja
#     D7 A2 EF BF BD 3A 20 EF BF BD -- the non-UTF-8 bytes replaced by U+FFFD.
#     Ninja compares bytes, so the prefix never matches: it echoes every
#     /showIncludes line instead of consuming it and records "#deps 0" for the
#     object. A minimal two-target Ninja experiment with an identical
#     msvc_deps_prefix confirms the split -- the compiler alone records the
#     header, the same compiler behind sccache records nothing.
#     The consequence is that editing a header does not rebuild its dependents.
#     Configure with -DEF_ENABLE_COMPILER_CACHE=OFF to trade the cache back for
#     correct incremental builds until the cache stops transcoding the stream.
# Separate-PDB configurations (/Zi, i.e. Debug and RelWithDebInfo) stay correct
# as well: when several translation units share one /Fd target PDB, sccache
# classifies the compiles it cannot replay safely as non-cacheable and runs the
# real compiler, so the shared PDB never loses a translation unit; it just
# caches less.
#
# Default OFF: ordinary incremental builds must keep compiler-produced header
# dependency data intact.  Pass -DEF_ENABLE_COMPILER_CACHE=ON only on a
# toolchain whose launcher is known to preserve that data.  An externally
# supplied CMAKE_<LANG>_COMPILER_LAUNCHER always wins over this block.
if (EF_ENABLE_COMPILER_CACHE
    AND NOT CMAKE_C_COMPILER_LAUNCHER
    AND NOT CMAKE_CXX_COMPILER_LAUNCHER)
    find_program(EF_COMPILER_CACHE_EXECUTABLE NAMES sccache ccache)
    mark_as_advanced(EF_COMPILER_CACHE_EXECUTABLE)
    if (EF_COMPILER_CACHE_EXECUTABLE)
        get_filename_component(EF_COMPILER_CACHE_NAME "${EF_COMPILER_CACHE_EXECUTABLE}" NAME_WE)
        if (MSVC
            AND CMAKE_GENERATOR MATCHES "Ninja"
            AND EF_COMPILER_CACHE_NAME STREQUAL "sccache")
            message(WARNING
                "Compiler cache disabled: sccache does not preserve localized "
                "MSVC /showIncludes dependencies for Ninja"
            )
        else()
            set(CMAKE_C_COMPILER_LAUNCHER "${EF_COMPILER_CACHE_EXECUTABLE}")
            set(CMAKE_CXX_COMPILER_LAUNCHER "${EF_COMPILER_CACHE_EXECUTABLE}")
            message(STATUS "Compiler cache: ${EF_COMPILER_CACHE_EXECUTABLE}")
        endif()
    endif()
endif()

if (CMAKE_RANLIB)
    # Ensure static archives get a symbol index on all toolchains.
    set(CMAKE_C_ARCHIVE_FINISH "<CMAKE_RANLIB> <TARGET>")
    set(CMAKE_CXX_ARCHIVE_FINISH "<CMAKE_RANLIB> <TARGET>")
endif()

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(Threads REQUIRED)

include(FetchContent)

# --- Pinned Dependency Re-Validation ---------------------------------------
# Every dependency below is pinned to an exact commit hash.  By default the git
# update step runs on each configure so a reused build tree cannot silently
# retain a checkout that differs from the declared pin.  That confirmation is
# not free.  With UPDATE_DISCONNECTED=FALSE the update step is marked ALWAYS,
# which forces the nested populate project to re-run its whole chain (update -> patch ->
# configure -> build -> install -> test) on every reconfigure.  Measured on this
# tree with CMake 3.31.6 + Ninja on Windows, each connected dependency costs
# 6.5-6.9 s of configure time, while nanobind -- the one declaration that had
# already opted into UPDATE_DISCONNECTED -- costs 1.6 s.
#
# CMake 3.27 fixed UPDATE_DISCONNECTED so a changed declaration re-runs the
# update step.  Older supported CMake versions can retain stale populated
# sources, so the performance opt-out is rejected there instead of weakening
# the pin contract.
if (NOT EF_FETCHCONTENT_REVALIDATE_PINS AND CMAKE_VERSION VERSION_LESS 3.27)
    message(FATAL_ERROR
        "EF_FETCHCONTENT_REVALIDATE_PINS=OFF requires CMake 3.27 or newer; "
        "older CMake versions can retain stale FetchContent revisions"
    )
endif()

if (EF_FETCHCONTENT_REVALIDATE_PINS)
    set(EF_FETCHCONTENT_PIN_MODE "")
else()
    set(EF_FETCHCONTENT_PIN_MODE UPDATE_DISCONNECTED TRUE)
endif()

# 1. Flecs (ECS)
FetchContent_Declare(
    flecs
    GIT_REPOSITORY https://github.com/SanderMertens/flecs.git
    GIT_TAG        eeb9eaa64243536c5d5c19279c9c305a52d0b9b3 # v4.0.0
    SOURCE_SUBDIR  __cmo_no_upstream_cmake_project__
    ${EF_FETCHCONTENT_PIN_MODE}
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
    ${EF_FETCHCONTENT_PIN_MODE}
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
FetchContent_Declare(
    nanobind
    GIT_REPOSITORY https://github.com/wjakob/nanobind.git
    GIT_TAG        80a30c8efb093b14f0e744bc7f6a9ef34beb3f7f # v1.9.2
    PATCH_COMMAND  "${CMAKE_COMMAND}"
                   "-DNANOBIND_DEFS_HEADER=<SOURCE_DIR>/include/nanobind/nb_defs.h"
                   -P "${CMAKE_CURRENT_SOURCE_DIR}/cmake/patches/nanobind_mingw_visibility.cmake"
    ${EF_FETCHCONTENT_PIN_MODE}
)
FetchContent_MakeAvailable(nanobind)

# 4. nlohmann_json (Config Loading)
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        9cca280a4d0ccf0c08f47a99aa71d1b0e52f8d03 # v3.11.3
    ${EF_FETCHCONTENT_PIN_MODE}
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
)

set(EF_CORE_MISSION_EPISODE_DETAIL_SOURCES
    src/core/mission/episode/detail/episode_reward_breakdown.cpp
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
    src/runtime/facade/runtime_facade_world_setup.cpp
    src/runtime/facade/runtime_facade_query.cpp
    src/runtime/facade/runtime_facade_command_api.cpp
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

set(EF_CORE_SOURCES
    ${EF_CORE_ENGINE_SOURCES}
    ${EF_CORE_GEOMETRY_SOURCES}
    ${EF_CORE_MISSION_SOURCES}
    ${EF_MODEL_DEFAULT_SOURCES}
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

# ef_content is listed first: ef_core's engine/model TUs call into the content
# loader (e.g. simulation_kernel.cpp -> default_unit_factory.h ->
# load_unit_definitions_json), and content never calls back, so ef_content must
# resolve after ef_core on a single-pass link line.  CMake derives that order
# from this dependency edge automatically for every downstream consumer.
target_link_libraries(ef_core PUBLIC
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
# T3 units (engine, mission) stay in one archive: splitting them is deferred
# to the T4 batch-wrapper design per the I41 allowlist verdicts.
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
    # bind_command() domain slices, listed in nanobind registration order.
    src/interfaces/python/bindings_command_enums.cpp
    src/interfaces/python/bindings_command_comm.cpp
    src/interfaces/python/bindings_command_pilot_report.cpp
    src/interfaces/python/bindings_command_pilot_action.cpp
    src/interfaces/python/bindings_command_mission_command.cpp
    src/interfaces/python/bindings_command_task_order.cpp
    src/interfaces/python/bindings_command_task_order_api.cpp
    src/interfaces/python/bindings_command_leader_intent.cpp
    src/interfaces/python/bindings_core.cpp
    # bind_core() domain slices, listed in nanobind registration order.
    src/interfaces/python/bindings_core_enums.cpp
    src/interfaces/python/bindings_core_instruments.cpp
    src/interfaces/python/bindings_core_weapon_profiles.cpp
    src/interfaces/python/bindings_core_unit_data.cpp
    src/interfaces/python/bindings_core_debug_views.cpp
    src/interfaces/python/bindings_core_observation.cpp
    src/interfaces/python/bindings_core_simulation_kernel.cpp
    # SimulationKernel method-surface slices, in the same registration order;
    # the diagnostics sub-slices follow their own orchestration shell.
    src/interfaces/python/bindings_core_kernel_maintained.cpp
    src/interfaces/python/bindings_core_kernel_diagnostics.cpp
    src/interfaces/python/bindings_core_kernel_diagnostics_views.cpp
    src/interfaces/python/bindings_core_kernel_diagnostics_platform_state.cpp
    src/interfaces/python/bindings_core_kernel_diagnostics_missile.cpp
    src/interfaces/python/bindings_core_kernel_legacy.cpp
    src/interfaces/python/bindings_core_kernel_override.cpp
    src/interfaces/python/bindings_episode.cpp
    # bind_episode() domain slices, listed in nanobind registration order.
    src/interfaces/python/bindings_episode_geometry.cpp
    src/interfaces/python/bindings_episode_mission_nav.cpp
    src/interfaces/python/bindings_episode_waypoint_approach.cpp
    src/interfaces/python/bindings_episode_flight_shaping.cpp
    src/interfaces/python/bindings_episode_objective.cpp
    src/interfaces/python/bindings_episode_termination.cpp
    src/interfaces/python/bindings_episode_execution_runtime.cpp
    src/interfaces/python/bindings_episode_state_batch.cpp
    src/interfaces/python/bindings_runtime.cpp
    # bind_runtime() domain slices, listed in nanobind registration order.
    src/interfaces/python/bindings_runtime_runtime.cpp
    src/interfaces/python/bindings_runtime_fidelity.cpp
    src/interfaces/python/bindings_runtime_platform.cpp
    src/interfaces/python/bindings_runtime_engagement.cpp
    # bind_runtime_engagement() sub-slices, in the same registration order.
    src/interfaces/python/bindings_runtime_engagement_events.cpp
    src/interfaces/python/bindings_runtime_engagement_damage.cpp
    src/interfaces/python/bindings_runtime_engagement_track_launch.cpp
    src/interfaces/python/bindings_runtime_engagement_munition.cpp
    src/interfaces/python/bindings_runtime_kill_chain.cpp
    src/interfaces/python/bindings_runtime_policy.cpp
    src/interfaces/python/bindings_runtime_batch_setup.cpp
    src/interfaces/python/bindings_runtime_experiment.cpp
    src/interfaces/python/bindings_runtime_batch_request.cpp
    src/interfaces/python/bindings_runtime_learning.cpp
    src/interfaces/python/bindings_runtime_batch_packet.cpp
    src/interfaces/python/bindings_runtime_tasking.cpp
    src/interfaces/python/bindings_runtime_window.cpp
    src/interfaces/python/bindings_runtime_platform_world.cpp
    src/interfaces/python/bindings_runtime_tasking_world.cpp
    src/interfaces/python/bindings_runtime_engine.cpp
    src/interfaces/python/bindings_runtime_facade.cpp
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
    target_compile_options(ef_cuda_resident_backend PRIVATE
        $<$<COMPILE_LANGUAGE:CUDA>:--ptxas-options=-v>
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

# The phase-0 probes are diagnostics entry points with no test, CI or tooling
# caller: the only references outside their own sources are the two
# tools/diagnostics READMEs, which already build them by name.  Each one
# still relinks the whole engine, and gpu_visual_candidate_phase0_probe.cpp
# does not even compile under MSVC (it calls __builtin_popcount), so leaving
# them in the default target made `cmake --build` fail on Windows for output
# nobody consumes.  EXCLUDE_FROM_ALL keeps every probe buildable by name.
add_executable(ef_gpu_visual_phase0_probe EXCLUDE_FROM_ALL
    src/tools/experimental/gpu_phase0/gpu_visual_phase0_probe.cpp
)
target_link_libraries(ef_gpu_visual_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_execution_observation_phase0_probe EXCLUDE_FROM_ALL
    src/tools/experimental/gpu_phase0/gpu_execution_observation_phase0_probe.cpp
)
target_link_libraries(ef_gpu_execution_observation_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_flight_shaping_phase0_probe EXCLUDE_FROM_ALL
    src/tools/experimental/gpu_phase0/gpu_flight_shaping_phase0_probe.cpp
)
target_link_libraries(ef_gpu_flight_shaping_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_interaction_broadphase_phase0_probe EXCLUDE_FROM_ALL
    src/tools/experimental/gpu_phase0/gpu_interaction_broadphase_phase0_probe.cpp
)
target_link_libraries(ef_gpu_interaction_broadphase_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_sensor_candidate_phase0_probe EXCLUDE_FROM_ALL
    src/tools/experimental/gpu_phase0/gpu_sensor_candidate_phase0_probe.cpp
)
target_link_libraries(ef_gpu_sensor_candidate_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_comm_candidate_phase0_probe EXCLUDE_FROM_ALL
    src/tools/experimental/gpu_phase0/gpu_comm_candidate_phase0_probe.cpp
)
target_link_libraries(ef_gpu_comm_candidate_phase0_probe PRIVATE
    ef_gpu_experiments
)

add_executable(ef_gpu_visual_candidate_phase0_probe EXCLUDE_FROM_ALL
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
    ${EF_FETCHCONTENT_PIN_MODE}
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
    # Only the CUDA-resident suites without a second home stay here.  The
    # lifecycle, state, device-consumer, performance and replay translation
    # units are compiled and run by ef_cuda_resident_lifecycle_test /
    # ef_cuda_resident_replay_test, which link nothing but
    # ef_cuda_resident_backend + doctest -- proof they need no ef_core symbol.
    # Listing them here too compiled each one a second time against the full
    # engine graph and made ctest execute the same doctest cases twice.
    src/tests/test_cuda_resident_backend_admission.cpp
    src/tests/test_cuda_resident_fixed_air_cpu_reference.cpp
    src/tests/test_cuda_resident_control_preparation_cpu_reference.cpp
    src/tests/test_cuda_resident_flight_dynamics_cpu_reference.cpp
    src/tests/test_world_batch_runtime.cpp
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
endif()

set(EF_PROJECT_WARNING_TARGETS
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
    ef_cuda_resident_lifecycle_test
    ef_cuda_resident_replay_test
    ef_cuda_resident_full_window_test
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
