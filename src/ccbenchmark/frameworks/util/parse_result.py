from __future__ import annotations
# Prevents circular imports
import ccbenchmark.benchmark_data as bd
from dataclasses import dataclass

@dataclass(slots=True)
class ParseResult:
    """Result from parse framework function.
    
    Returned by a generator specifying the value of a cell within benchmark_data.

    Attributes:
        real_time: Time it takes based off a real clock.
        cpu_time: Time it takes based off the cpu clock.

        name: The name of the benchmark that was run.
        metric_index: The column that this result belongs to.
    """
    real_time: bd.BenchmarkTime
    cpu_time: bd.BenchmarkTime

    name: str
    metric_index: int