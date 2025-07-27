#include "benchmark/benchmark.h"
#include <unistd.h>

static void bm_1(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.003);
    }
}

BENCHMARK(bm_1)->Repetitions(3)->MinTime(0.5);
BENCHMARK_MAIN();