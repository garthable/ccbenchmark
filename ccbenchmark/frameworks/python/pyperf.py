from pathlib import Path
from ccbenchmark.frameworks.util.parse_result import ParseResult
from ccbenchmark.benchmark_data import BenchmarkTime, TimeUnit
from io import TextIOWrapper
from typing import Generator

import json
import math

import ccbenchmark.benchmark_settings as settings
import subprocess

from enum import IntEnum

NON_AGGREGATED_METRICS = []
AGGREGATED_METRICS = ['Mean', 'Median', 'Stddev']
SUPPORTED_FORMATS = {'json'}

class MetricIndex(IntEnum):
    Mean = 0


def run_single_benchmark(binary_path: Path, output_path: Path) -> int:
    output_path.unlink(missing_ok=True)

    cmd = [
        'python3',
        binary_path, 
        f'-o={output_path}', 
        f'--quiet'
    ]

    return subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=False)

def parse(file_stream: TextIOWrapper, file_path: Path) -> Generator[ParseResult, None, None]:
    json_contents: dict = json.load(file_stream)
    benchmarks: list[dict] = json_contents.get('benchmarks')
    if benchmarks is None:
        return
    for benchmark in benchmarks:
        metadata: dict = benchmark.get('metadata')
        if metadata is None:
            continue
        name = metadata.get('name')
        if name is None:
            continue
        runs: list[dict] = benchmark.get('runs')
        if runs is None:
            continue
        all_values: list[float] = []
        for run in runs:
            values: list[float] = run.get('values')
            if values is None:
                continue
            all_values += values
        n = len(all_values)
        median_value = sorted(all_values)[n // 2]
        median = BenchmarkTime(median_value, TimeUnit.S)
        yield ParseResult(median, median, name, 1, True)
        mean_value = 0.0
        for value in all_values:
            mean_value += value / n
        mean = BenchmarkTime(mean_value, TimeUnit.S)
        yield ParseResult(mean, mean, name, 0, True)
        stddev_value = 0.0
        for value in all_values:
            stddev_value += (value - mean_value)**2
        stddev_value /= n
        stddev_value = math.sqrt(stddev_value)
        stddev = BenchmarkTime(stddev_value, TimeUnit.S)
        yield ParseResult(stddev, stddev, name, 2, True)