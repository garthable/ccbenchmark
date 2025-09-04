from enum import IntEnum, StrEnum
from dataclasses import dataclass, field
from typing import Optional
import logging
from pathlib import Path
from ccbenchmark.util import strip_common_paths
import math
from copy import deepcopy
from typing import Callable
from io import TextIOWrapper

from ccbenchmark.benchmark_framework import Framework

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

@dataclass(slots=True, init=False)
class BenchmarkTime:
    _time_value: float | None
    time_unit: TimeUnit | None

    def __init__(self, time_value: float | None, time_unit: TimeUnit | None):
        if time_value is not None and time_value == 0.0:
            min_float_value = math.ulp(0.0)
            self._time_value = min_float_value
        else:
            self._time_value = time_value
        self.time_unit = time_unit

    @property
    def time_value(self) -> float:
        assert self._time_value is None or self._time_value != 0.0
        return self._time_value
    
    @time_value.setter
    def time_value(self, value: float) -> None:
        min_float_value = math.ulp(0.0)
        self._time_value = value if value != 0.0 else min_float_value
    
    def __str__(self) -> str:
        return f'{self.time_value:.2F} {self.time_unit}' if self.time_value is not None else 'N/A'

def convert_time(benchmark_time: BenchmarkTime, time_unit: TimeUnit) -> BenchmarkTime:
    if benchmark_time.time_unit is None or benchmark_time.time_unit is TimeUnit.PERCENTAGE or time_unit is None:
        return benchmark_time
    
    assert type(benchmark_time) is BenchmarkTime, f'Type Error! type(benchmark_time) is {type(benchmark_time).__name__}'
    assert type(time_unit) is TimeUnit, f'Type Error! type(time_unit) is {type(time_unit).__name__}'
    
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
    if not converted_other_time or not base_time:
        return BenchmarkTime(None, None)
    if not converted_other_time.time_value or not base_time.time_value:
        return BenchmarkTime(None, None)
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
    real_time: BenchmarkTime = field(default_factory=lambda: BenchmarkTime(None, None))
    real_time_comparisons: list[BenchmarkTime] = field(default_factory=lambda: [])
    
    cpu_time: BenchmarkTime = field(default_factory=lambda: BenchmarkTime(None, None))
    cpu_time_comparisons: list[BenchmarkTime] = field(default_factory=lambda: [])

    def segment_str(self, time_type: TimeType, min_amount: int) -> list[str]:
        if time_type is TimeType.CPU:
            segment_str = [str(self.cpu_time)] + [str(cpu_time) for cpu_time in self.cpu_time_comparisons]
        else:
            segment_str = [str(self.real_time)] + [str(real_time) for real_time in self.real_time_comparisons]
        extra_elements = max(0, min_amount - len(segment_str))
        return segment_str + [str(BenchmarkTime(None, None)) for _ in range(extra_elements)]

@dataclass(init=False, slots=True)
class BenchmarkIterations:
    times: list[list[BenchmarkSegment]]
    runnable_path: Path | None
    recent_index: int | None

    def __init__(self, metric_count: int, iteration_count: int, runnable_path: Path | None):
        self.times: list[list[BenchmarkSegment]] = [
            [BenchmarkSegment(
                BenchmarkTime(None, None), [], 
                BenchmarkTime(None, None), []) 
                for _ in range(metric_count
            )] 
            for _ in range(iteration_count)
        ]
        self.runnable_path: Path | None = runnable_path
        self.recent_index = None

    @property
    def recent(self) -> list[BenchmarkSegment]:
        if self.recent_index is None:
            for i, row in reversed(list(enumerate(self.times))):
                if not all(entry.cpu_time.time_value is None and entry.real_time.time_value is None for entry in row):
                    self.recent_index = i
                    break
            assert self.recent_index is not None, f'Cannot find valid recent index for {self.runnable_path}'

        return self.times[self.recent_index]
    
    @property
    def metric_count(self) -> int:
        return len(self.times[0]) if len(self.times) else 0
    
    @property
    def iteration_count(self) -> int:
        return len(self.times)

@dataclass(slots=True)
class MetricName:
    name: str
    name_comparisons: list[str] = field(default_factory=lambda: [])

@dataclass(init=False, slots=True)
class BenchmarkData:
    benchmark_names: list[str]
    iteration_names: list[str]
    benchmarks: list[BenchmarkIterations]
    metric_names: list[MetricName]
    benchmark_name_to_index: dict[(Path, str), int]

    def __init__(self, iteration_names: list[str]):
        self.benchmark_names: list[str] = []
        self.iteration_names: list[str] = iteration_names
        self.benchmarks: list[BenchmarkIterations] = []
        self.benchmark_name_to_index: dict[(Path, str), int] = {}

        metric_names = ['Time', 'μ', 'Stddev', 'Med', 'Mad', 'Min', 'Max', 'CV']
        self.metric_names: list[MetricName] = [MetricName(metric_name) for metric_name in metric_names]
    
    def add_file(self, iteration_index: int, file_stream: TextIOWrapper, file_path: Path, benchmark_path: Path, framework: Framework) -> None:
        """Adds file to BenchmarkData"""
        metric_count = len(self.metric_names)
        iteration_count = len(self.iteration_names)

        for parse_result in framework.parse(file_stream, file_path):
            benchmark_id = (benchmark_path, parse_result.name)
            if benchmark_id not in self.benchmark_name_to_index:
                benchmark_index = len(self.benchmarks)
                self.benchmark_name_to_index[benchmark_id] = benchmark_index
                benchmark = BenchmarkIterations(metric_count, iteration_count, benchmark_path)
                self.benchmarks.append(benchmark)
                self.benchmark_names.append(parse_result.name)
            else:
                benchmark_index = self.benchmark_name_to_index[benchmark_id]
            
            assert benchmark_index < len(self.benchmarks), f'Benchmark Index is out of bounds. {benchmark_index} < {len(self.benchmarks)}'

            iterations = self.benchmarks[benchmark_index]
            iterations.runnable_path = benchmark_path

            assert iteration_index < iterations.iteration_count, f'Iteration Index is out of bounds. {iteration_index} < {iterations.iteration_count}'
            assert parse_result.metric_index < iterations.metric_count, f'Metric Index is out of bounds. {parse_result.metric_index} < {iterations.metric_count}'

            segment = iterations.times[iteration_index][parse_result.metric_index]
            segment.cpu_time = parse_result.cpu_time
            segment.real_time = parse_result.real_time

    def validate(self) -> None:
        assert len(self.benchmarks) == len(self.benchmark_names), f'len({self.benchmarks} != len({self.benchmark_names}))'
        for benchmark, name in zip(self.benchmarks, self.benchmark_names):
            assert benchmark.runnable_path is not None
            assert \
                not all(entry.cpu_time.time_value is None and entry.real_time.time_value is None for row in benchmark.times for entry in row),\
                f'{name} is empty!'
            
            assert \
                not all(entry.cpu_time.time_value is None and entry.real_time.time_value is None for entry in benchmark.recent),\
                f'{name} recent is empty!'

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
            if max_exps == []:
                continue
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
        time_unit: TimeUnit | None = None
        for benchmark in self.benchmarks:
            prev_metrics = [BenchmarkSegment() for _ in self.metric_names]
            for metrics in benchmark.times:
                for metric, prev_metric in zip(metrics, prev_metrics):
                    time = metric.cpu_time if time_type is TimeType.CPU else metric.real_time
                    base_time = prev_metric.cpu_time if time_type is TimeType.CPU else prev_metric.real_time

                    time_unit = time_unit or base_time.time_unit

                    comparison_time = compare(time, base_time, comparison_func)
                    if time_type is TimeType.CPU:
                        metric.cpu_time_comparisons.append(comparison_time)
                    else:
                        metric.real_time_comparisons.append(comparison_time)
                    assert \
                        len(metric.cpu_time_comparisons) > 0 or \
                        len(metric.real_time_comparisons) > 0, \
                        f'append did not occur! cpu: {metric.cpu_time_comparisons} real: {metric.real_time_comparisons}'
                    if time.time_value is not None:
                        base_time.time_value = time.time_value
                        base_time.time_unit = time.time_unit

    def compare_recent_iterations(self,
            comparison_func: Callable[[BenchmarkTime, BenchmarkTime], BenchmarkTime],
            selected_benchmark_indicies: list[int],
            time_type: TimeType
        ) -> None:
        assert len(selected_benchmark_indicies) != 0
        self.reset(time_type)
        time_unit: TimeUnit | None = None
        
        base_index = selected_benchmark_indicies[0]
        base_benchmark = self.benchmarks[base_index].recent
        for benchmark_index in selected_benchmark_indicies[1:]:
            benchmark = self.benchmarks[benchmark_index].recent
            for i, (metric, base_metric) in enumerate(zip(benchmark, base_benchmark)):
                time = metric.cpu_time if time_type is TimeType.CPU else metric.real_time
                base_time = base_metric.cpu_time if time_type is TimeType.CPU else base_metric.real_time

                time_unit = time_unit or base_time.time_unit

                comparison_time = compare(time, base_time, comparison_func)
                if time_type is TimeType.CPU:
                    benchmark[i].cpu_time_comparisons.append(comparison_time)
                else:
                    benchmark[i].real_time_comparisons.append(comparison_time)

    def strip_common_paths(self) -> None:
        paths = [benchmark.runnable_path for benchmark in self.benchmarks]
        paths = strip_common_paths(paths)
        for i, _ in enumerate(self.benchmarks):
            self.benchmarks[i].runnable_path = paths[i]
    
    def update(self, selected_column_indices: list[int], time_type: TimeType):
        if len(selected_column_indices) == 0:
            return
        if len(selected_column_indices) == 1:
            for metric_name in self.metric_names:
                metric_name.name_comparisons = [f'Δ{metric_name.name} ()']
            self.compare_neighboring_iterations(compute_delta_percentage, time_type)
            return
        
        base_index = selected_column_indices[0]
        for metric_name in self.metric_names:
            metric_name.name_comparisons = [f'Δ{metric_name.name}@{self.benchmark_names[base_index]} ()']
        self.compare_recent_iterations(compute_delta_percentage, selected_column_indices, time_type)

    def column_to_str_matrix(self, selected_column_indices: list[int], time_type: TimeType) -> list[list[str]]:
        matrix: list[list[str]] = []
        if len(selected_column_indices) == 0:
            return []
        main_index = selected_column_indices[0]
        main_benchmark = self.benchmarks[main_index]

        metric_count = len(self.metric_names)

        items_per_comparison = max(len(name.name_comparisons) + 1 for name in self.metric_names)
        min_elements = items_per_comparison * metric_count

        def get_row(entry: list[BenchmarkSegment]) -> list[str]:
            segment_indicies = range(len(self.metric_names))
            row = [val for i in segment_indicies for val in entry[i].segment_str(time_type, items_per_comparison)]
            row += ['N/A' for _ in range(max(0, min_elements - len(row)))]
            assert len(row) == min_elements, f'Mismatch in elements! len({row}) != {min_elements}'
            return row

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

        columns = []
        for i, _ in enumerate(self.metric_names):
            columns += [self.metric_names[i].name] + self.metric_names[i].name_comparisons

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
            assert benchmark.runnable_path is not None
            for part in benchmark.runnable_path.parts:
                next_dict: dict | None = current_dict.get(part)
                if next_dict is None:
                    current_dict[part] = {}
                    next_dict = current_dict[part]
                current_dict = next_dict
            current_dict[benchmark_name] = i
        return data_dict
    
def load_benchmark_data(iteration_names_to_index: dict[str, int], iteration_paths_and_frameworks: list[tuple[Path, Framework]]) -> BenchmarkData:
    benchmark_data = BenchmarkData(list(iteration_names_to_index.keys()))

    for iteration_path, framework in iteration_paths_and_frameworks:
        name = iteration_path.name[len('_iter_'):]
        iteration_index = iteration_names_to_index[name]
        assert iteration_path.is_dir(), f'{iteration_path} is not a directory.'
        for file_path in iteration_path.iterdir():
            with open(file_path, 'r', encoding='locale') as file_stream:
                benchmark_path = iteration_path.parent / file_path.name.split('.')[0]
                benchmark_data.add_file(iteration_index, file_stream, file_path, benchmark_path, framework)
    
    benchmark_data.validate()
    benchmark_data.establish_common_time_unit()
    benchmark_data.strip_common_paths()
    
    return benchmark_data