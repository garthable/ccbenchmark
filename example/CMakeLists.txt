add_executable(benchmark_0 benchmark0.cpp)
add_executable(benchmark_1 benchmark1.cpp)

target_link_libraries(benchmark_0 PUBLIC benchmark_main)
target_link_libraries(benchmark_1 PUBLIC benchmark_main)

add_benchmark(benchmark_0)
add_benchmark(benchmark_1)
end_add_benchmark()