cmake_minimum_required(VERSION 3.20)
project(EchelonForge VERSION 0.2.0 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
option(EF_ENABLE_CUDA_EXPERIMENTS "Enable experimental CUDA GPU runtime scaffolding" OFF)
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
    GIT_TAG        v4.0.0
)
FetchContent_MakeAvailable(flecs)

# 2. spdlog (Logging)
FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG        v1.13.0
)
FetchContent_MakeAvailable(spdlog)

# 3. nanobind (Python Bindings)
FetchContent_Declare(
    nanobind
    GIT_REPOSITORY https://github.com/wjakob/nanobind.git
    GIT_TAG        v1.9.2
)
FetchContent_MakeAvailable(nanobind)

# 4. nlohmann_json (Config Loading)
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        v3.11.3
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
    src/core/mission/runtime/execution_frame_runtime.cpp
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
)

set(EF_CORE_SOURCES
    ${EF_CORE_ENGINE_SOURCES}
    ${EF_CORE_GEOMETRY_SOURCES}
    ${EF_CORE_MISSION_SOURCES}
    ${EF_RUNTIME_FACADE_SOURCES}
    ${EF_MODEL_DEFAULT_SOURCES}
    ${EF_CONTENT_SOURCES}
)

# --- Core Library ---
add_library(ef_core STATIC
    ${EF_CORE_SOURCES}
)

target_include_directories(ef_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(ef_core PUBLIC
    flecs::flecs
    spdlog::spdlog
    nlohmann_json::nlohmann_json
    Threads::Threads
)

# --- Standalone App ---
# We keep src/main.cpp for local C++ testing, but now it needs to include/use SimulationKernel
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
target_link_libraries(ef_py PRIVATE ef_core)

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

if (EF_ENABLE_CUDA_EXPERIMENTS)
    enable_language(CUDA)
    find_package(CUDAToolkit REQUIRED)
    list(APPEND EF_GPU_EXPERIMENT_SOURCES
        src/gpu/gpu_visual_runtime_cuda.cu
        src/gpu/gpu_execution_observation_runtime_cuda.cu
        src/gpu/gpu_flight_shaping_runtime_cuda.cu
        src/gpu/gpu_interaction_broadphase_runtime_cuda.cu
    )
endif()

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
FetchContent_Declare(
    doctest
    GIT_REPOSITORY https://github.com/doctest/doctest.git
    GIT_TAG        v2.4.11
)
FetchContent_MakeAvailable(doctest)

enable_testing()

set(EF_TEST_SOURCES
    src/tests/test_main.cpp
    src/tests/test_simulation_kernel_smoke.cpp
    src/tests/test_components_basic.cpp
    src/tests/test_aero_physics_common.cpp
    src/tests/test_kalman_seeker.cpp
    src/tests/test_structural_failure_system.cpp
    src/tests/test_control_surface_damage_coupling.cpp
    src/tests/test_world_batch_runtime.cpp
    src/tests/test_default_effects_model.cpp
)

add_executable(ef_test ${EF_TEST_SOURCES})
target_link_libraries(ef_test PRIVATE ef_core ef_gpu_experiments doctest::doctest)
target_include_directories(ef_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)

# CTest entries for all doctest suites plus focused structural-failure lanes.
add_test(NAME ef_test_all COMMAND ef_test)
add_test(NAME structural_failure_state COMMAND ef_test --test-suite=structural_failure_state)
add_test(NAME structural_failure_events COMMAND ef_test --test-suite=structural_failure_events)
add_test(NAME structural_failure_break_modes COMMAND ef_test --test-suite=structural_failure_break_modes)
add_test(NAME structural_consequence COMMAND ef_test --test-suite=structural_consequence)
add_test(NAME aircraft_damage_lifecycle COMMAND ef_test --test-suite=aircraft_damage_lifecycle)
add_test(NAME world_batch_runtime COMMAND ef_test --test-suite=world_batch_runtime)
add_test(NAME default_effects_model COMMAND ef_test --test-suite=default_effects_model)
set_tests_properties(default_effects_model PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

set(EF_PROJECT_WARNING_TARGETS
    ef_core
    ef_app
    ef_py
    ef_gpu_experiments
    ef_gpu_visual_phase0_probe
    ef_gpu_execution_observation_phase0_probe
    ef_gpu_flight_shaping_phase0_probe
    ef_gpu_interaction_broadphase_phase0_probe
    ef_gpu_sensor_candidate_phase0_probe
    ef_gpu_comm_candidate_phase0_probe
    ef_gpu_visual_candidate_phase0_probe
    ef_test
)

foreach(target_name IN LISTS EF_PROJECT_WARNING_TARGETS)
    if (TARGET ${target_name})
        ef_enable_project_warnings(${target_name})
    endif()
endforeach()

# Install the extension module
install(TARGETS ef_py DESTINATION .)
set_target_properties(ef_py PROPERTIES INSTALL_RPATH "$ORIGIN/lib")
