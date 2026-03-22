cmake_minimum_required(VERSION 3.20)
project(EchelonForge VERSION 0.1.0 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

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

# --- Core Library ---
add_library(ef_core STATIC
    src/core/engine/simulation_kernel.cpp
    src/core/engine/world_batch_runtime.cpp
    src/core/geometry/spatial_query_runtime.cpp
    src/core/mission/execution_observation_runtime.cpp
    src/core/mission/mission_runtime.cpp
    src/core/mission/execution_step_runtime.cpp
    src/core/mission/execution_frame_runtime.cpp
    src/core/mission/execution_episode_runtime.cpp
    src/core/mission/reward_runtime.cpp
    src/core/mission/objective_runtime.cpp
    src/core/mission/termination_runtime.cpp
    src/models/weapons/default_effects_model.cpp
    src/models/systems/default_sensor_model.cpp
    src/models/environment/default_environment_model.cpp
    src/content/unit_definition_loader.cpp
    src/models/air/default_control_model.cpp
    src/models/weapons/default_guidance_model.cpp
    # Add other core source files here if they become cpp
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

# --- Python Module ---
nanobind_add_module(ef_py src/interfaces/python/python_module.cpp)
target_link_libraries(ef_py PRIVATE ef_core)

# Install the extension module
install(TARGETS ef_py DESTINATION .)
set_target_properties(ef_py PROPERTIES INSTALL_RPATH "$ORIGIN/lib")
