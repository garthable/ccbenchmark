from typing import Protocol, Callable, Generator
from pathlib import Path
from ccbenchmark.parsers.util.parse_result import ParseResult

class Parser(Protocol):
    NON_AGGREGATED_METRICS: list[str]
    AGGREGATED_METRICS: list[str]

    get_benchmark_path: Callable[[dict], Path]
    parse: Callable[[dict], Generator[ParseResult, None, None]]