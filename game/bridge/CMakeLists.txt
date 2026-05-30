cmake_minimum_required(VERSION 3.20)
project(echelon_bridge VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(echelon_bridge SHARED
    src/echelon_bridge.cpp
)

target_compile_definitions(echelon_bridge PRIVATE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
    _WINSOCK_DEPRECATED_NO_WARNINGS
)

target_include_directories(echelon_bridge PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(echelon_bridge PRIVATE
    ws2_32
)

set_target_properties(echelon_bridge PROPERTIES
    OUTPUT_NAME "echelon_bridge"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../mod/@EchelonProxy"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../mod/@EchelonProxy"
)
