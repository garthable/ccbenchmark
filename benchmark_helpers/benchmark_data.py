from enum import IntEnum

class TimeType(IntEnum):
    REAL_TIME_INDEX = 0
    CPU_TIME_INDEX = 1

class BenchmarkTime:
    def __init__(
        self,
        real_time: float | None = None,
        real_time_delta: float | None = None,
        cpu_time: float | None = None,
        cpu_time_delta: float | None = None,
        time_unit: str | None = None
    ):
        self.time: list[float | None] = [real_time, cpu_time]
        self.time_delta: list[float | None] = [real_time_delta, cpu_time_delta]
        self.time_unit: str | None = time_unit

class BenchmarkEntry:
    def __init__(
        self, 
        iteration: str | None = None,
        time: BenchmarkTime = BenchmarkTime(), 
        mean_time: BenchmarkTime = BenchmarkTime(), 
        median_time: BenchmarkTime = BenchmarkTime(),
        stddev_time: BenchmarkTime = BenchmarkTime(),
        cv_time: BenchmarkTime = BenchmarkTime()
    ):
        self.iteration: str | None = iteration
        self.time: BenchmarkTime = time
        self.mean_time: BenchmarkTime = mean_time 
        self.median_time: BenchmarkTime = median_time
        self.stddev_time: BenchmarkTime = stddev_time
        self.cv_time: BenchmarkTime = cv_time
    
    def get_row(self, is_aggregated: bool, time_type: TimeType) -> list[str]:
        row = [self.iteration]
        if not is_aggregated:
            time = self.time.time[time_type]
            time_delta = self.time.time_delta[time_type]
            time_unit = self.time.time_unit
            row.append(f'{time:.2f} {time_unit}' if time is not None else 'N/A')
            row.append(f'{time_delta:.2f}%' if time_delta is not None else 'N/A')
            return row

        mean = self.mean_time.time[time_type]
        mean_delta = self.mean_time.time_delta[time_type]
        time_unit = self.mean_time.time_unit
        row.append(f'{mean:.2f} {time_unit}' if mean is not None else 'N/A')
        row.append(f'{mean_delta:.2f}%' if mean_delta is not None else 'N/A')

        median = self.median_time.time[time_type]
        median_delta = self.median_time.time_delta[time_type]
        time_unit = self.median_time.time_unit
        row.append(f'{median:.2f} {time_unit}' if median is not None else 'N/A')
        row.append(f'{median_delta:.2f}%' if median_delta is not None else 'N/A')

        stddev = self.stddev_time.time[time_type]
        stddev_delta = self.stddev_time.time_delta[time_type]
        time_unit = self.stddev_time.time_unit
        row.append(f'{stddev:.2f} {time_unit}' if stddev is not None else 'N/A')
        row.append(f'{stddev_delta:.2f}%' if stddev_delta is not None else 'N/A')

        cv = self.cv_time.time[time_type]
        cv_delta = self.cv_time.time_delta[time_type]
        row.append(f'{cv:.2f}%' if cv is not None else 'N/A')
        row.append(f'{cv_delta:.2f}%' if cv_delta is not None else 'N/A')

        return row

    
class BenchmarkColumn:
    def __init__(self, aggregated: bool = False):
        self.data: list[BenchmarkEntry] = []
        self.aggregated = aggregated

    def __iter__(self):
        for d in self.data:
            yield d

    def __setitem__(self, i, item):
        self.data[i] = item

    def __getitem__(self, i):
        return self.data[i]

    def append(self, entry: BenchmarkEntry | None):
        self.data.append(entry)

class BenchmarkData:
    def __init__(self, benchmark_names: list[str], iteration_names: list[str]):
        self.benchmark_names: list[str] = benchmark_names
        self.iteration_names: list[str] = iteration_names
        self.matrix: list[BenchmarkColumn] = []

        for i in range(len(benchmark_names)):
            self.matrix.append(BenchmarkColumn())
            for name in iteration_names:
                self.matrix[i].append(BenchmarkEntry(iteration=name))
    
    def add_json_file(self, iteration_index, json_file, benchmark_name_to_index: dict[str, int]):
        for benchmark in json_file['benchmarks']:
            name = benchmark['run_name']
            index = benchmark_name_to_index.get(name)

            if index is None:
                continue

            real_time = benchmark['real_time']
            cpu_time = benchmark['cpu_time']
            time_unit = benchmark['time_unit']
            repetitions = benchmark['repetitions']
            run_type = benchmark['run_type']

            time = BenchmarkTime(real_time=real_time, cpu_time=cpu_time, time_unit=time_unit)
            iteration_name = self.iteration_names[iteration_index]

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

    def compute_delta(self):
        for col in self.matrix:
            if not col.aggregated:
                prev_time = BenchmarkTime()
                for entry in col.data:
                    for time_type in [TimeType.REAL_TIME_INDEX, TimeType.CPU_TIME_INDEX]:
                        new_value = entry.time.time[time_type]
                        old_value = prev_time.time[time_type]

                        if new_value is None or old_value is None:
                            continue

                        entry.time.time_delta[time_type] = ((new_value - old_value) / old_value) * 100.0

                    prev_time = entry.time
                continue

            prev_times = [BenchmarkTime() for i in range(4)]
            for entry in col.data:
                curr_times = [entry.mean_time, entry.median_time, entry.stddev_time, entry.cv_time]
                for prev_time, curr_time in zip(prev_times, curr_times):
                    for time_type in [TimeType.REAL_TIME_INDEX, TimeType.CPU_TIME_INDEX]:
                        new_value = curr_time.time[time_type]
                        old_value = prev_time.time[time_type]

                        if new_value is None or old_value is None:
                            continue

                        curr_time.time_delta[time_type] = ((new_value - old_value) / old_value) * 100.0

                prev_times = curr_times

        