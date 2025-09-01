from __future__ import annotations
import ccbenchmark.benchmark_data as bd
from dataclasses import dataclass
from typing import Any

@dataclass(slots=True)
class ParseResult:
    real_time: bd.BenchmarkTime
    cpu_time: bd.BenchmarkTime

    name: str
    metric_index: int

    aggregated: bool