from typing import Generator, Any
from pathlib import Path
import logging

from ccbenchmark.benchmark_data import BenchmarkTime, TimeUnit
from ccbenchmark.parsers.util.default_metrics import (
    NON_AGGREGATED_METRICS, AGGREGATED_METRICS, MetricIndices
)
from ccbenchmark.parsers.util.parse_result import ParseResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def get_benchmark_path(json_file: dict) -> Path:
    try:
        benchmark_bin_line = json_file['context']['executable']
    except KeyError:
        logger.warning(f"Missing '[context][executable]' in JSON file. Failed to add JSON file.")
        return Path()
    
    return Path(benchmark_bin_line)

def parse(json_file: dict) -> Generator[ParseResult, None, None]:
    """Adds json file to BenchmarkData"""
    try:
        benchmarks = json_file['benchmarks']
    except KeyError:
        logger.warning(f"Missing 'benchmarks' in JSON file. Failed to add JSON file.")
        return
    
    benchmark_bin_path = get_benchmark_path(json_file)

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

        benchmark_id = (benchmark_bin_path, name)
        if benchmark_id is None:
            logger.debug(f"{name} not found in benchmark_name_to_index")
            continue

        real_time = BenchmarkTime(real_time_value, time_unit)
        cpu_time = BenchmarkTime(cpu_time_value, time_unit)

        if repetitions == 1 and run_type == 'iteration':
            yield ParseResult(real_time, cpu_time, benchmark_id, MetricIndices.Time.value, aggregated=False)
            continue

        if run_type == 'aggregate':
            aggregate_name = benchmark['aggregate_name']
            if aggregate_name == 'mean':
                yield ParseResult(real_time, cpu_time, benchmark_id, MetricIndices.Mean.value, aggregated=True)
            elif aggregate_name == 'median':
                yield ParseResult(real_time, cpu_time, benchmark_id, MetricIndices.Median.value, aggregated=True)
            elif aggregate_name == 'stddev':
                yield ParseResult(real_time, cpu_time, benchmark_id, MetricIndices.Stddev.value, aggregated=True)
            elif aggregate_name == 'cv':
                real_time.time_unit = TimeUnit.PERCENTAGE
                real_time.time_value *= 100.0

                cpu_time.time_unit = TimeUnit.PERCENTAGE
                cpu_time.time_value *= 100.0

                yield ParseResult(real_time, cpu_time, benchmark_id, MetricIndices.CV.value, aggregated=True)
            else:
                logger.warning(f"Unknown aggregate_name: {run_type}")