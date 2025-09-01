add_executable(benchmark_0 benchmark0.cpp)
add_executable(benchmark_1 benchmark1.cpp)
add_executable(benchmark_2 benchmark1.cpp)

target_link_libraries(benchmark_0 PUBLIC benchmark_main)
target_link_libraries(benchmark_1 PUBLIC benchmark_main)
target_link_libraries(benchmark_2 PUBLIC benchmark_main)

set_target_properties(benchmark_2
    PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/build/example/other_dir")