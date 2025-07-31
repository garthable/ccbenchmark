from enum import IntEnum
from dataclasses import dataclass
from typing import Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGGREGATE_KINDS = ['mean', 'median', 'stddev', 'cv']

class TimeType(IntEnum):
    REAL = 0
    CPU = 1

@dataclass(init=False)
class BenchmarkTime:
    __slots__ = ("times", "time_deltas", "time_unit")

    def __init__(
        self,
        real_time: Optional[float] = None,
        real_time_delta: Optional[float] = None,
        cpu_time: Optional[float] = None,
        cpu_time_delta: Optional[float] = None,
        time_unit: Optional[str] = None
    ):
        self.times = [real_time, cpu_time]
        self.time_deltas = [real_time_delta, cpu_time_delta]
        self.time_unit = time_unit

    def __repr__(self) -> str:
        return f"BenchmarkTime(real={self.real_time}, real_time_delta={self.real_time_delta}, cpu={self.cpu_time}, cpu_time_delta={self.cpu_time_delta}, unit={self.time_unit})"

    @property
    def real_time(self) -> Optional[float]:
        return self.times[TimeType.REAL]

    @real_time.setter
    def real_time(self, value: Optional[float]):
        self.times[TimeType.REAL] = value

    @property
    def cpu_time(self) -> Optional[float]:
        return self.times[TimeType.CPU]

    @cpu_time.setter
    def cpu_time(self, value: Optional[float]):
        self.times[TimeType.CPU] = value

    @property
    def real_time_delta(self) -> Optional[float]:
        return self.time_deltas[TimeType.REAL]

    @real_time_delta.setter
    def real_time_delta(self, value: Optional[float]):
        self.time_deltas[TimeType.REAL] = value

    @property
    def cpu_time_delta(self) -> Optional[float]:
        return self.time_deltas[TimeType.CPU]

    @cpu_time_delta.setter
    def cpu_time_delta(self, value: Optional[float]):
        self.time_deltas[TimeType.CPU] = value

class BenchmarkEntry:
    __slots__ = ("iteration", "time", "mean_time", "median_time", "stddev_time", "cv_time")
    def __init__(
        self, 
        iteration: Optional[str] = None,
        time: Optional[BenchmarkTime] = None, 
        mean_time: Optional[BenchmarkTime] = None, 
        median_time: Optional[BenchmarkTime] = None,
        stddev_time: Optional[BenchmarkTime] = None,
        cv_time: Optional[BenchmarkTime] = None
    ):
        self.iteration: Optional[str] = iteration
        self.time: BenchmarkTime = time or BenchmarkTime()
        self.mean_time: BenchmarkTime = mean_time or BenchmarkTime()
        self.median_time: BenchmarkTime = median_time or BenchmarkTime()
        self.stddev_time: BenchmarkTime = stddev_time or BenchmarkTime()
        self.cv_time: BenchmarkTime = cv_time or BenchmarkTime()

    def __repr__(self) -> str:
        return f"BenchmarkEntry(iteration={self.iteration}, time={self.time}, mean_time={self.mean_time}, median_time={self.median_time}, stddev_time={self.stddev_time}, cv_time={self.cv_time})"
    
    def get_row(self, is_aggregated: bool, time_type: TimeType) -> list[str]:
        """Gets BenchmarkEntry as a row of strings."""
        row = [self.iteration]
        if not is_aggregated:
            time = self.time.times[time_type]
            time_delta = self.time.time_deltas[time_type]
            time_unit = self.time.time_unit
            row.append(f'{time:.2f} {time_unit}' if time is not None else 'N/A')
            row.append(f'{time_delta:.2f} %' if time_delta is not None else 'N/A')
            return row

        aggregate_times = [self.mean_time, self.median_time, self.stddev_time]
        for time in aggregate_times:
            value = time.times[time_type]
            delta = time.time_deltas[time_type]
            time_unit = time.time_unit
            row.append(f'{value:.2f} {time_unit}' if value is not None else 'N/A')
            row.append(f'{delta:.2f} %' if delta is not None else 'N/A')

        cv = self.cv_time.times[time_type]
        cv_delta = self.cv_time.time_deltas[time_type]
        row.append(f'{cv:.2f} %' if cv is not None else 'N/A')
        row.append(f'{cv_delta:.2f} %' if cv_delta is not None else 'N/A')

        return row

class BenchmarkColumn:
    __slots__ = ("data", "benchmark_bin_path", "aggregated")
    def __init__(self, benchmark_bin_path: Optional[Path] = None, aggregated: bool = False):
        self.data: list[BenchmarkEntry] = []
        self.benchmark_bin_path: Optional[Path] = benchmark_bin_path
        self.aggregated = aggregated

    def __iter__(self):
        return iter(self.data)

    def __setitem__(self, i: int, item: BenchmarkEntry) -> None:
        self.data[i] = item

    def __getitem__(self, i: int) -> BenchmarkEntry:
        return self.data[i]

    def __len__(self) -> int:
        return len(self.data)

    def append(self, entry: Optional[BenchmarkEntry]) -> None:
        self.data.append(entry)

class BenchmarkData:
    __slots__ = ("benchmark_names", "iteration_names", "matrix")
    def __init__(self, benchmark_names: list[str], iteration_names: list[str]):
        self.benchmark_names: list[str] = benchmark_names
        self.iteration_names: list[str] = iteration_names
        self.matrix: list[BenchmarkColumn] = []

        for i in range(len(benchmark_names)):
            self.matrix.append(BenchmarkColumn())
            for name in iteration_names:
                self.matrix[i].append(BenchmarkEntry(iteration=name))
    
    def add_json_file(self, iteration_index: int, json_file: dict, benchmark_name_to_index: dict[tuple[Path, str], int]) -> None:
        """Adds json file to BenchmarkData"""
        try:
            benchmarks = json_file['benchmarks']
        except KeyError:
            logger.warning(f"Missing 'benchmarks' in JSON file. Failed to add JSON file.")
            return
        try:
            benchmark_bin_line = json_file['context']['executable']
        except KeyError:
            logger.warning(f"Missing '[context][executable]' in JSON file. Failed to add JSON file.")
            return
        
        benchmark_bin_path = Path(benchmark_bin_line)

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
                name = get_value('run_name')
                real_time = get_value('real_time')
                cpu_time = get_value('cpu_time')
                time_unit = get_value('time_unit')
                repetitions = get_value('repetitions')
                run_type = get_value('run_type')
            except SkipBenchmark:
                continue

            index = benchmark_name_to_index.get((benchmark_bin_path, name))
            if index is None:
                logger.debug(f"{name} not found in benchmark_name_to_index")
                continue

            time = BenchmarkTime(real_time=real_time, cpu_time=cpu_time, time_unit=time_unit)
            iteration_name = self.iteration_names[iteration_index]
            self.matrix[index].benchmark_bin_path = benchmark_bin_path

            if repetitions == 1 and run_type == 'iteration':
                self.matrix[index].aggregated = False
                entry = BenchmarkEntry(iteration=iteration_name, time=time)
                self.matrix[index][iteration_index] = entry
                continue

            if run_type == 'aggregate':
                self.matrix[index].aggregated = True
                aggregate_name = benchmark['aggregate_name']
                self.matrix[index][iteration_index].iteration = iteration_name
                if aggregate_name == 'mean':
                    self.matrix[index][iteration_index].mean_time = time
                elif aggregate_name == 'median':
                    self.matrix[index][iteration_index].median_time = time
                elif aggregate_name == 'stddev':
                    self.matrix[index][iteration_index].stddev_time = time
                elif aggregate_name == 'cv':
                    self.matrix[index][iteration_index].cv_time = time
                else:
                    logger.warning(f"Unknown aggregate_name: {run_type}")

    def compute_delta(self) -> None:
        """Computes percentage change between iterations."""
        for col in self.matrix:
            if not col.aggregated:
                prev_time = BenchmarkTime()
                for entry in col.data:
                    for time_type in [TimeType.REAL, TimeType.CPU]:
                        new_value = entry.time.times[time_type]
                        old_value = prev_time.times[time_type]

                        if new_value is None or old_value is None or old_value == 0.0:
                            continue

                        entry.time.time_deltas[time_type] = ((new_value - old_value) / old_value) * 100.0

                    prev_time = entry.time
                continue
            
            prev_times = [BenchmarkTime() for _ in AGGREGATE_KINDS]
            for entry in col.data:
                curr_times = [entry.mean_time, entry.median_time, entry.stddev_time, entry.cv_time]
                for prev_time, curr_time in zip(prev_times, curr_times):
                    for time_type in [TimeType.REAL, TimeType.CPU]:
                        new_value = curr_time.times[time_type]
                        old_value = prev_time.times[time_type]

                        if new_value is None or old_value is None:
                            continue

                        curr_time.time_deltas[time_type] = ((new_value - old_value) / old_value) * 100.0

                prev_times = curr_times

    def strip_common_paths(self) -> None:
        paths = [col.benchmark_bin_path for col in self.matrix]
        max_iterations = min([len(path.parts) for path in paths])

        for _ in range(max_iterations):
            common_part = None
            for path in paths:
                assert(len(path.parts) != 0)
                part = path.parts[0]
                if common_part is None:
                    common_part = part
                elif common_part != part:
                    for i in range(len(self.matrix)):
                        self.matrix[i].benchmark_bin_path = paths[i]
                    return

            for j in range(len(paths)):
                parts = paths[j].parts[1:]
                paths[j] = Path(*parts)
        raise Exception("Reached maximum path part depth!")  