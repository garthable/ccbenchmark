#include "benchmark/benchmark.h"

static void bm(benchmark::State& state)
{
    for (auto _ : state)
    {
        for (int i = 0; i < 1'000'000; i++)
        {
            benchmark::DoNotOptimize(i);
        }
    }
}

static void bm_9(benchmark::State& state)
{
    for (auto _ : state)
    {
        for (int i = 0; i < 1'000'000'000; i++)
        {
            benchmark::DoNotOptimize(i);
        }
    }
}

static void bm_10(benchmark::State& state)
{
    for (auto _ : state)
    {
        for (long long i = 0; i < 10'000'000'000; i++)
        {
            benchmark::DoNotOptimize(i);
        }
    }
}

static void bm_label(benchmark::State& state)
{
    for (auto _ : state)
    {
        for (int i = 0; i < 1'000'000; i++)
        {
            benchmark::DoNotOptimize(i);
        }
    }
}

static void bm_unit_set(benchmark::State& state)
{
    for (auto _ : state)
    {
        for (int i = 0; i < 1'000'000; i++)
        {
            benchmark::DoNotOptimize(i);
        }
    }
}

BENCHMARK(bm)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_9)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_10)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_label)->Repetitions(3)->MinTime(0.5)->Name("bm_label");
BENCHMARK(bm_unit_set)->Repetitions(3)->MinTime(0.5)->Unit(benchmark::TimeUnit::kSecond);
BENCHMARK_MAIN();