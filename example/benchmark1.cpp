#include "benchmark/benchmark.h"
#include <unistd.h>

static void bm_1(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.003);
    }
}

static void bm_2(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.0003);
    }
}

static void bm_3(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.00003);
    }
}

static void bm_4(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.000003);
    }
}

static void bm_5(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.0000003);
    }
}

static void bm_6(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.000000003);
    }
}

static void bm_7(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.0000000003);
    }
}

static void bm_8(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.00000000003);
    }
}

static void bm_9(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.000000000003);
    }
}

static void bm_10(benchmark::State& state)
{
    for (auto _ : state)
    {
        sleep(0.000000000000003);
    }
}

BENCHMARK(bm_1)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_2)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_3)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_4)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_5)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_6)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_7)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_8)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_9)->Repetitions(3)->MinTime(0.5);
BENCHMARK(bm_10)->Repetitions(3)->MinTime(0.5);
BENCHMARK_MAIN();