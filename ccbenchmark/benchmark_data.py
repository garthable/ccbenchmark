from enum import IntEnum, StrEnum
from dataclasses import dataclass
from typing import Optional
import logging
from pathlib import Path
from ccbenchmark.util import time_to_str
import math
from copy import deepcopy
from typing import Callable, cast
import importlib
from ccbenchmark.parsers.util.parser_protocol import Parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

class TimeUnit(StrEnum):
    NS = 'ns'
    US = 'us'
    MS = 'ms'
    S = 's'
    PERCENTAGE = '%'

class TimeType(IntEnum):
    REAL = 0
    CPU = 1

@dataclass(slots=True)
class BenchmarkTime:
    time_value: float | None
    time_unit: TimeUnit | None
    
    def __str__(self) -> str:
        return f'{self.time_value:.2F} {self.time_unit}' if self.time_value else 'N/A'

def convert_time(benchmark_time: BenchmarkTime, time_unit: TimeUnit) -> BenchmarkTime:
    assert type(benchmark_time) is BenchmarkTime, f'Type Error! type(benchmark_time) is {type(benchmark_time).__name__}'
    assert type(time_unit) is TimeUnit, f'Type Error! type(time_unit) is {type(time_unit).__name__}'

    if benchmark_time.time_unit is None or benchmark_time.time_unit is TimeUnit.PERCENTAGE:
        return benchmark_time
    
    time_unit_to_exponent = {TimeUnit.NS: 0, TimeUnit.US: 3, TimeUnit.MS: 6, TimeUnit.S: 9}

    input_unit = time_unit_to_exponent[benchmark_time.time_unit]
    output_unit = time_unit_to_exponent[time_unit]

    conversion_exponent = input_unit - output_unit
    converted_benchmark_time = deepcopy(benchmark_time)
    
    converted_benchmark_time.time_unit = time_unit

    scaler = math.log(float(10**conversion_exponent))
    log_sum = math.fsum([math.log(converted_benchmark_time.time_value) + scaler])
    converted_benchmark_time.time_value = math.exp(log_sum)
    return converted_benchmark_time

def compare(other_time: BenchmarkTime, base_time: BenchmarkTime, func: Callable[[BenchmarkTime, BenchmarkTime], BenchmarkTime]) -> BenchmarkTime:
    converted_other_time = convert_time(other_time, base_time.time_unit)
    return func(converted_other_time, base_time)

def compute_delta_percentage(other_time: BenchmarkTime, base_time: BenchmarkTime) -> BenchmarkTime:
    log_fraction = math.fsum([math.log(other_time.time_value), -math.log(base_time.time_value)])
    delta = math.expm1(log_fraction)
    return BenchmarkTime(
        delta * 100.0,
        TimeUnit.PERCENTAGE
    )

@dataclass(slots=True)
class BenchmarkSegment:
    real_time: BenchmarkTime
    real_time_comparisons: list[BenchmarkTime]
    
    cpu_time: BenchmarkTime
    cpu_time_comparisons: list[BenchmarkTime]

    def segment_str(self, time_type: TimeType) -> list[str]:
        if time_type is TimeType.CPU:
            return [str(self.cpu_time)] + [str(cpu_time) for cpu_time in self.cpu_time_comparisons]
        else:
            return [str(self.real_time)] + [str(real_time) for real_time in self.real_time_comparisons]

@dataclass(init=False, slots=True)
class BenchmarkIterations:
    times: list[list[BenchmarkSegment]]
    bin_path: Path | None
    aggregated: Path | None

    def __init__(self, metric_count: int, iteration_count: int, bin_path: Path | None, aggregated: bool):
        self.times: list[list[BenchmarkSegment]] = [
            [BenchmarkSegment(
                BenchmarkTime(None, None), [], 
                BenchmarkTime(None, None), []) 
                for _ in range(metric_count
            )] 
            for _ in range(iteration_count)
        ]
        self.bin_path: Path | None = bin_path
        self.aggregated: bool = aggregated

    @property
    def recent(self) -> list[BenchmarkSegment]:
        return self.times[len(self.times) - 1]
    
    @property
    def metric_count(self) -> int:
        return len(self.times[0]) if len(self.times) else 0
    
    @property
    def iteration_count(self) -> int:
        return len(self.times)

@dataclass(init=False, slots=True)
class BenchmarkData:
    benchmark_names: list[str]
    iteration_names: list[str]
    benchmarks: list[BenchmarkIterations]
    parser: Parser
    metric_names: list[list[str]]

    def __init__(self, benchmark_names: list[str], iteration_names: list[str]):
        self.benchmark_names: list[str] = benchmark_names
        self.iteration_names: list[str] = iteration_names
        self.benchmarks: list[BenchmarkIterations] = []

        self.parser = cast(Parser, importlib.import_module('ccbenchmark.parsers.cpp.google_benchmark'))

        metric_names = self.parser.AGGREGATED_METRICS + self.parser.NON_AGGREGATED_METRICS
        self.metric_names: list[list[str]] = [[metric_name] for metric_name in metric_names]
        iteration_count = len(self.iteration_names)
        metric_count = len(metric_names)

        for _ in range(len(benchmark_names)):
            self.benchmarks.append(BenchmarkIterations(metric_count, iteration_count, None, False))
    
    def add_json_file(self, iteration_index: int, json_file: dict, benchmark_name_to_index: dict[tuple[Path, str], int]) -> None:
        """Adds json file to BenchmarkData"""
        benchmark_bin_path: Path = self.parser.get_executable_path(json_file)

        for parse_result in self.parser.parse(json_file, benchmark_name_to_index, benchmark_bin_path):
            assert parse_result.benchmark_index < len(self.benchmarks), f'Benchmark Index is out of bounds. {parse_result.benchmark_index} < {len(self.benchmarks)}'

            iterations = self.benchmarks[parse_result.benchmark_index]
            iterations.bin_path = benchmark_bin_path

            iterations.aggregated = parse_result.aggregated

            assert iteration_index < iterations.iteration_count, f'Iteration Index is out of bounds. {iteration_index} < {iterations.iteration_count}'
            assert parse_result.metric_index < iterations.metric_count, f'Metric Index is out of bounds. {parse_result.metric_index} < {iterations.metric_count}'

            segment = iterations.times[iteration_index][parse_result.metric_index]
            segment.cpu_time = parse_result.cpu_time
            segment.real_time = parse_result.real_time

    def establish_common_time_unit(self) -> None:
        self._establish_common_time_unit(time_type=TimeType.CPU)
        self._establish_common_time_unit(time_type=TimeType.REAL)

    def _establish_common_time_unit(self, time_type: TimeType) -> None:
        for benchmark in self.benchmarks:
            times = []
            for segment in benchmark.recent:
                times.append(segment.real_time if time_type is TimeType.REAL else segment.cpu_time)
                times += segment.real_time_comparisons if time_type is TimeType.REAL else segment.cpu_time_comparisons

            max_exps = []
            for time in times:
                copy_time = convert_time(time, TimeUnit.NS)
                if copy_time.time_value is None:
                    continue
                max_exps.append(math.log10(copy_time.time_value))
            assert max_exps != [], f'Max Exponents cannot be empty'
            max_exp = int(max(max_exps))

            if max_exp < 3:
                time_unit = TimeUnit.NS
            elif max_exp < 6:
                time_unit = TimeUnit.US
            elif max_exp < 9:
                time_unit = TimeUnit.MS
            else:
                time_unit = TimeUnit.S
                
            for iteration in benchmark.times:
                for metric_index, metric in enumerate(iteration):
                    if time_type is TimeType.CPU:
                        iteration[metric_index].cpu_time = convert_time(metric.cpu_time, time_unit)
                    else:
                        iteration[metric_index].real_time = convert_time(metric.real_time, time_unit)

    def reset(self, time_type: TimeType):
        for benchmark in self.benchmarks:
            for metrics in benchmark.times:
                for metric in metrics:
                    if time_type is TimeType.CPU:
                        metric.cpu_time_comparisons = []
                    else:
                        metric.real_time_comparisons = []

    def compare_neighboring_iterations(self, 
            comparison_func: Callable[[BenchmarkTime, BenchmarkTime], BenchmarkTime],
            time_type: TimeType
        ) -> None:
        """Computes percentage change between iterations."""
        self.reset(time_type)
        for benchmark in self.benchmarks:
            for index, _ in enumerate(benchmark.times, start=1):
                prev_metrics = benchmark.times[index - 1]
                metrics = benchmark.times[index]

                for metric, prev_metric in zip(metrics, prev_metrics):
                    time = metric.cpu_time if time_type is TimeType.CPU else metric.real_time
                    base_time = prev_metric.cpu_time if time_type is TimeType.CPU else prev_metric.real_time

                    comparison_time = comparison_func(time, base_time)
                    if time_type is TimeType.CPU:
                        metric.cpu_time_comparisons.append(comparison_time)
                    else:
                        metric.real_time_comparisons.append(comparison_time)

    def compare_recent_iterations(self,
            comparison_func: Callable[[BenchmarkTime, BenchmarkTime], BenchmarkTime],
            selected_benchmark_indicies: list[int],
            time_type: TimeType
        ) -> None:
        assert len(selected_benchmark_indicies) != 0
        self.reset(time_type)

        base_index = selected_benchmark_indicies[0]
        base_benchmark = self.benchmarks[base_index].recent
        for benchmark_index in selected_benchmark_indicies[1:]:
            benchmark = self.benchmarks[benchmark_index].recent
            for metric, base_metric in zip(benchmark, base_benchmark):
                time = metric.cpu_time if time_type is TimeType.CPU else metric.real_time
                base_time = base_metric.cpu_time if time_type is TimeType.CPU else base_metric.real_time

                comparison_time = comparison_func(time, base_time)
                if time_type is TimeType.CPU:
                    metric.cpu_time_comparisons.append(comparison_time)
                else:
                    metric.real_time_comparisons.append(comparison_time)

    def strip_common_paths(self) -> None:
        paths = [benchmark.bin_path for benchmark in self.benchmarks]
        max_iterations = min([len(path.parts) for path in paths])

        for _ in range(max_iterations):
            common_part = None
            for path in paths:
                assert(len(path.parts) != 0)
                part = path.parts[0]
                if common_part is None:
                    common_part = part
                elif common_part != part:
                    for i, _ in enumerate(self.benchmarks):
                        self.benchmarks[i].bin_path = paths[i]
                    return

            for j in range(len(paths)):
                parts = paths[j].parts[1:]
                paths[j] = Path(*parts)
        raise Exception("Reached maximum path part depth!")  
    
    def column_to_str_matrix(self, selected_column_indices: list[int], time_type: TimeType) -> list[list[str]]:
        aggregated = False
        for index in selected_column_indices:
            aggregated = aggregated or self.benchmarks[index].aggregated

        matrix: list[list[str]] = []
        if len(selected_column_indices) == 0:
            return []
        main_index = selected_column_indices[0]
        main_benchmark = self.benchmarks[main_index]

        def get_row(entry: list[BenchmarkSegment]) -> list[str]:
            aggregated_len = len(self.parser.AGGREGATED_METRICS)
            non_aggregated_len = len(self.parser.NON_AGGREGATED_METRICS)

            aggregated_range = range(non_aggregated_len, non_aggregated_len + aggregated_len)
            non_aggregated_range = range(non_aggregated_len)

            segment_indicies = non_aggregated_range if not aggregated else aggregated_range
            return [val for i in segment_indicies for val in entry[i].segment_str(time_type)]

        if len(selected_column_indices) == 1:
            for entry in main_benchmark.times:
                row = get_row(entry)
                assert type(row) is list, f'row is {type(row).__name__}'
                for val in row:
                    assert type(val) is str, f'val is {type(val).__name__}'
                matrix.append(row)
            return matrix
        
        recent_entry = main_benchmark.recent
        matrix.append(get_row(recent_entry))

        for i in selected_column_indices[1:]:
            other_column = self.benchmarks[i]
            other_entry = other_column.recent
            matrix.append(get_row(other_entry))
        return matrix
    
    def get_columns(self, selected_column_indices: list[int]) -> list[str]:
        if len(selected_column_indices) == 0:
            return []
        
        aggregated = False
        for index in selected_column_indices:
            aggregated = aggregated or self.benchmarks[index].aggregated

        if not aggregated:
            columns = self.parser.NON_AGGREGATED_METRICS
        else:
            columns = self.parser.AGGREGATED_METRICS

        return columns

    def get_rows(self, selected_column_indices: list[int]) -> list[str]:
        if len(selected_column_indices) == 0:
            return []
        elif len(selected_column_indices) == 1:
            return self.iteration_names
        return [self.benchmark_names[i] for i in selected_column_indices]
    
    def data_to_dict(self) -> dict:
        data_dict = {}
        for i, (benchmark, benchmark_name) in enumerate(zip(self.benchmarks, self.benchmark_names)):
            current_dict = data_dict
            for part in benchmark.bin_path.parts:
                next_dict: dict | None = data_dict.get(part)
                if next_dict is None:
                    current_dict[part] = {}
                    next_dict = current_dict[part]
                current_dict = next_dict
            current_dict[benchmark_name] = i
        return data_dict