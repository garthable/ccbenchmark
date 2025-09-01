import ccbenchmark.benchmark_settings as settings
import importlib
from ccbenchmark.frameworks.util.parse_result import ParseResult
from typing import cast, Protocol, Generator, Callable
from pathlib import Path

class Framework(Protocol):
    NON_AGGREGATED_METRICS: list[str]
    AGGREGATED_METRICS: list[str]
    OUTPUT_SUFFIX: str

    run_single_benchmark: Callable[[Path, Path], int]
    parse: Callable[[dict], Generator[ParseResult, None, None]]

framework: Framework = None

def import_framework() -> None:
    global framework
    framework = cast(Framework, importlib.import_module(f'ccbenchmark.frameworks.{settings.local_settings.framework}'))

    assert hasattr(framework, 'NON_AGGREGATED_METRICS')
    assert isinstance(framework.NON_AGGREGATED_METRICS, list)

    assert hasattr(framework, 'AGGREGATED_METRICS')
    assert isinstance(framework.AGGREGATED_METRICS, list)

    assert hasattr(framework, 'OUTPUT_SUFFIX')
    assert isinstance(framework.OUTPUT_SUFFIX, str)

    assert hasattr(framework, 'run_single_benchmark')
    assert isinstance(framework.run_single_benchmark, Callable)

    assert hasattr(framework, 'parse')
    assert isinstance(framework.parse, Callable)