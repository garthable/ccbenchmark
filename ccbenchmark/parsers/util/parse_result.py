from ccbenchmark.benchmark_data import BenchmarkTime
from dataclasses import dataclass

@dataclass(slots=True)
class ParseResult:
    real_time: BenchmarkTime
    cpu_time: BenchmarkTime

    benchmark_index: int
    metric_index: int

    aggregated: bool