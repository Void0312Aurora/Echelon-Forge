cmake_minimum_required(VERSION 3.20)
project(CMO VERSION 0.1.0 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

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

# --- Core Library ---
add_library(cmo_core STATIC
    src/core/simulation_kernel.cpp
    # Add other core source files here if they become cpp
)

target_include_directories(cmo_core PUBLIC 
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(cmo_core PUBLIC
    flecs::flecs
    spdlog::spdlog
)

# --- Standalone App ---
# We keep src/main.cpp for local C++ testing, but now it needs to include/use SimulationKernel
add_executable(cmo_app src/main.cpp)
target_link_libraries(cmo_app PRIVATE cmo_core)

# --- Python Module ---
nanobind_add_module(cmo_py src/bindings/python_module.cpp)
target_link_libraries(cmo_py PRIVATE cmo_core)
