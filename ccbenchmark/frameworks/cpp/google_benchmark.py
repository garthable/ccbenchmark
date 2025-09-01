from typing import Generator, Any
from pathlib import Path
import logging
import subprocess

from ccbenchmark.benchmark_data import BenchmarkTime, TimeUnit
from ccbenchmark.frameworks.util.default_metrics import (
    NON_AGGREGATED_METRICS, AGGREGATED_METRICS, MetricIndices
)
from ccbenchmark.frameworks.util.parse_result import ParseResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

OUTPUT_SUFFIX = '.json'

def run_single_benchmark(binary_path: Path, output_path: Path) -> int:
    """Runs a single benchmark binary and writes output to the given path."""
    cmd = [
        binary_path, 
        f'--benchmark_out={output_path}', 
        '--benchmark_out_format=json', 
        '--benchmark_report_aggregates_only=false'
    ]

    return subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=False)

def parse(json_file: dict) -> Generator[ParseResult, None, None]:
    """Adds json file to BenchmarkData"""
    try:
        benchmarks = json_file['benchmarks']
    except KeyError:
        logger.warning(f"Missing 'benchmarks' in JSON file. Failed to add JSON file.")
        return

    for benchmark in benchmarks:
        class SkipBenchmark(Exception):
            pass

        def get_value(key: str) -> any:
            try:
                value = benchmark[key]
            except KeyError:
                logger.warning(f"Missing '{key}' in JSON file. Failed to add entry.")
                raise SkipBenchmark()
            return value
        
        try:
            name: str = get_value('run_name')
            real_time_value: float = get_value('real_time')
            cpu_time_value: float = get_value('cpu_time')
            time_unit: str = get_value('time_unit')
            repetitions: int = get_value('repetitions')
            run_type: str = get_value('run_type')
        except SkipBenchmark:
            continue

        real_time = BenchmarkTime(real_time_value, time_unit)
        cpu_time = BenchmarkTime(cpu_time_value, time_unit)

        if repetitions == 1 and run_type == 'iteration':
            yield ParseResult(real_time, cpu_time, name, MetricIndices.Time.value, aggregated=False)
            continue

        if run_type == 'aggregate':
            aggregate_name = benchmark['aggregate_name']
            if aggregate_name == 'mean':
                yield ParseResult(real_time, cpu_time, name, MetricIndices.Mean.value, aggregated=True)
            elif aggregate_name == 'median':
                yield ParseResult(real_time, cpu_time, name, MetricIndices.Median.value, aggregated=True)
            elif aggregate_name == 'stddev':
                yield ParseResult(real_time, cpu_time, name, MetricIndices.Stddev.value, aggregated=True)
            elif aggregate_name == 'cv':
                real_time.time_unit = TimeUnit.PERCENTAGE
                real_time.time_value *= 100.0

                cpu_time.time_unit = TimeUnit.PERCENTAGE
                cpu_time.time_value *= 100.0

                yield ParseResult(real_time, cpu_time, name, MetricIndices.CV.value, aggregated=True)
            else:
                logger.warning(f"Unknown aggregate_name: {run_type}")