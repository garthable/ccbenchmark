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

# -------------------------------
# Benchmark List Accumulator
# (Use normal variable — NOT CACHE)
# -------------------------------
set(_BENCHMARK_ENTRIES "")

# -------------------------------
# Functions
# -------------------------------
function(add_benchmark TARGET_NAME)
    set(entry "$<TARGET_FILE:${TARGET_NAME}>")
    # Append the entry in parent scope
    set(_BENCHMARK_ENTRIES "${_BENCHMARK_ENTRIES}${entry}\n" PARENT_SCOPE)
endfunction()

set(BENCHMARK_PY ${CMAKE_CURRENT_SOURCE_DIR}/benchmark.py)
set(BENCHMARK_HELPERS_PY ${CMAKE_CURRENT_SOURCE_DIR}/benchmark_helpers)

function(end_add_benchmark)
    cmake_parse_arguments(BM
        ""
        "WORKING_DIRECTORY"
        ""
        ${ARGN}
    )

    if(NOT BM_WORKING_DIRECTORY)
        set(BM_WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}")
    endif()

    configure_file(${BENCHMARK_PY} ${BM_WORKING_DIRECTORY} COPYONLY)
    file(COPY ${BENCHMARK_HELPERS_PY} DESTINATION ${BM_WORKING_DIRECTORY})

    file(WRITE "${CMAKE_BINARY_DIR}/benchmark_setup.bash" 
    "#!/bin/bash \
    \nalias cbenchmark='python3 ${BM_WORKING_DIRECTORY}/benchmark.py -w ${BM_WORKING_DIRECTORY}'
    ")

    file(GENERATE
        OUTPUT "${BM_WORKING_DIRECTORY}/benchmarks.txt"
        CONTENT "${_BENCHMARK_ENTRIES}"
    )
endfunction()

add_subdirectory(example)