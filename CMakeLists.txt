cmake_minimum_required(VERSION 3.28)
project(benchmark_tool)

# -------------------------------
# Google Benchmark Fetch Setup
# -------------------------------
set(BENCHMARK_ENABLE_TESTING OFF)
set(BENCHMARK_INSTALL_DOCS OFF)

include(FetchContent)
FetchContent_Declare(
    googlebenchmark
    GIT_REPOSITORY https://github.com/google/benchmark.git
    GIT_TAG        f02794a8bda1295ed7a6c99615f8b79e6188d7f8
)
FetchContent_MakeAvailable(googlebenchmark)

include(FetchContent)
FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        d33ecd3f3bd11e30aa8bbabb00e0a9cd3f2456d8
)
FetchContent_MakeAvailable(json)

# -------------------------------
# Set default build type
# -------------------------------
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Build type" FORCE)
endif()

add_subdirectory(example)