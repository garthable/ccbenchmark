#include "benchmark/benchmark.h"
#include <unistd.h>

static void bm_0(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.002);
    }
}

static void bmbmbmbm(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.001);
    }
}

static void bm_1(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(1);
    }
}

BENCHMARK(bm_0);
BENCHMARK(bmbmbmbm);
BENCHMARK(bm_1)->Unit(benchmark::TimeUnit::kSecond);
BENCHMARK_MAIN();