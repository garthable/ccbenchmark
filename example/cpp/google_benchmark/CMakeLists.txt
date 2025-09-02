cmake_minimum_required(VERSION 3.28)
project(cpp_google_benchmark_example)

set(BENCHMARK_ENABLE_TESTING OFF)
set(BENCHMARK_INSTALL_DOCS OFF)

include(FetchContent)
FetchContent_Declare(
    googlebenchmark
    GIT_REPOSITORY https://github.com/google/benchmark.git
    GIT_TAG        f02794a8bda1295ed7a6c99615f8b79e6188d7f8
)
FetchContent_MakeAvailable(googlebenchmark)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Build type" FORCE)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(benchmark_0 benchmark_0.cpp)
add_executable(benchmark_1 benchmark_1.cpp)
add_executable(benchmark_2 benchmark_1.cpp)

target_link_libraries(benchmark_0 PUBLIC benchmark_main)
target_link_libraries(benchmark_1 PUBLIC benchmark_main)
target_link_libraries(benchmark_2 PUBLIC benchmark_main)

set_target_properties(benchmark_2
    PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/build/other_dir")