"""Stores data from benchmarks.

Defines:
    - TimeUnit: Time units used by program.
    - TimeType: Real or CPU time.
    - BenchmarkTime: Contains float and time unit.
    - MetricName: Contains metric base name and its comparisons.
    - BenchmarkData: Contains data, row names, and column names.
    - load_benchmark_data(): Loads benchmark from files.
"""

from enum import IntEnum, StrEnum
from dataclasses import dataclass, field
import logging
from pathlib import Path
from ccbenchmark.util import strip_common_paths
import math
from io import TextIOWrapper

from ccbenchmark.benchmark_framework import Framework
from ccbenchmark._ccbenchmark import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

class TimeUnit(StrEnum):
    """Time Untis used by ccbenchmark"""
    NS = 'ns'
    US = 'us'
    MS = 'ms'
    S = 's'
    PERCENTAGE = '%'

class TimeType(IntEnum):
    """Time Types used by ccbenchmark"""
    REAL = 0
    CPU = 1

@dataclass(slots=True, init=False)
class BenchmarkTime:
    """Stores time and time unit."""
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

@dataclass(slots=True)
class MetricName:
    name: str
    name_comparisons: list[str] = field(default_factory=lambda: [])

@dataclass(init=False, slots=True)
class BenchmarkData:
    benchmark_names: list[str]
    benchmark_paths: list[Path]
    iteration_names: list[str]
    benchmark_types: list[Manager]
    metric_names: list[MetricName]
    benchmark_name_to_index: dict[(Path, str), int]

    def __init__(self, iteration_names: list[str]):
        self.benchmark_names: list[str] = []
        self.benchmark_paths: list[Path] = []
        self.iteration_names: list[str] = iteration_names
        self.benchmark_types: list[Manager] = [Manager(), Manager()]
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
                benchmark_index = len(self.benchmark_paths)
                self.benchmark_name_to_index[benchmark_id] = benchmark_index

                for benchmark_type in self.benchmark_types:
                    benchmark_type.emplace(metric_count, iteration_count, "ns")

                self.benchmark_paths.append(benchmark_path)
                self.benchmark_names.append(parse_result.name)
            else:
                benchmark_index = self.benchmark_name_to_index[benchmark_id]

            self.benchmark_types[TimeType.CPU].set(
                benchmark_index, parse_result.metric_index, iteration_index, 
                parse_result.cpu_time.time_value or float("nan"), parse_result.cpu_time.time_unit or "")
            
            self.benchmark_types[TimeType.REAL].set(
                benchmark_index, parse_result.metric_index, iteration_index, 
                parse_result.real_time.time_value or float("nan"), parse_result.real_time.time_unit or "")

    def strip_common_paths(self) -> None:
        self.benchmark_paths = strip_common_paths(self.benchmark_paths)
    
    def update_metric_names(self, time_units: list[TimeUnit]) -> None:
        prefixes = ['', 'Δ']
        i = 0
        assert len(self.metric_names)*len(prefixes) == len(time_units),\
            f'len(prefixes) = {len(prefixes)}\n len(self.metric_names) = {len(self.metric_names)}\n len(time_units) = {len(time_units)}'
        for metric_name in self.metric_names:
            metric_name.name_comparisons = []
        for metric_name in self.metric_names:
            for prefix in prefixes:
                if i >= len(time_units):
                    break
                time_unit = time_units[i]
                metric_name.name_comparisons.append(f'{prefix}{metric_name.name} ({time_unit if time_unit is not None else ''})')
                i += 1

    def column_to_str_matrix(self, selected_column_indices: list[int], time_type: TimeType) -> list[list[str]]:
        profile = Profile()
        profile.selected_indicies = selected_column_indices
        profile.unit = "ns"

        return self.benchmark_types[time_type].run_profile(profile)
    
    def get_columns(self, selected_column_indices: list[int]) -> list[str]:
        if len(selected_column_indices) == 0:
            return []

        self.update_metric_names(['ns', '%', 'ns', '%', 'ns', '%', 'ns', '%', 'ns', '%', 'ns', '%', 'ns', '%', '%', '%'])
        columns = []
        for i, _ in enumerate(self.metric_names):
            columns += self.metric_names[i].name_comparisons

        return columns

    def get_rows(self, selected_column_indices: list[int]) -> list[str]:
        if len(selected_column_indices) == 0:
            return []
        elif len(selected_column_indices) == 1:
            return self.iteration_names
        return [self.benchmark_names[i] for i in selected_column_indices]
    
    def data_to_dict(self) -> dict:
        data_dict = {}
        for i, (path, benchmark_name) in enumerate(zip(self.benchmark_paths, self.benchmark_names)):
            current_dict = data_dict
            assert path is not None
            for part in path.parts:
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
    
    benchmark_data.strip_common_paths()
    
    return benchmark_data