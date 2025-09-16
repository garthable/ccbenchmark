import importlib
from ccbenchmark.frameworks.util.parse_result import ParseResult
from typing import cast, Protocol, Generator, Callable
from pathlib import Path
from io import TextIOWrapper

class Framework(Protocol):
    """Protocol defining the interface of a benchmark framework.

    A Framework must provide:
        - SUPPORTED_FORMATS: set of output formats it can generate.
        - run_single_benchmark(): run a single benchmark and write results.
        - parse(): parse benchmark output files into structured results.
    """
    SUPPORTED_FORMATS: set[str]

    def run_single_benchmark(
        runnable_path: Path, 
        output_location: Path, 
        output_format: str
    ) -> int: ...
    def parse(
        file_stream: TextIOWrapper, 
        path_to_file_opened: Path
    ) -> Generator[ParseResult, None, None]: ...

def import_framework(framework_name: str, output_format: str) -> Framework:
    """Import a benchmark framework for running and parsing benchmarks.

    Loads the framework module from `ccbenchmark.frameworks` and checks
    that it supports the requested output format and implements the
    required interface (`SUPPORTED_FORMATS`, `run_single_benchmark`, `parse`).

    Args:
        framework_name: Name of the framework module to import 
            (e.g., "cpp.google_benchmark", "python.pyperf").
        output_format: Desired output format (e.g., "json", "csv", "yaml"). 
            Must be supported by the framework.

    Returns:
        Framework: Module implementing `parse` and `run_single_benchmark`.
    """
    framework = cast(Framework, importlib.import_module(f'ccbenchmark.frameworks.{framework_name}'))

    assert hasattr(framework, 'SUPPORTED_FORMATS')
    assert isinstance(framework.SUPPORTED_FORMATS, set)

    assert output_format in framework.SUPPORTED_FORMATS

    assert hasattr(framework, 'run_single_benchmark')
    assert isinstance(framework.run_single_benchmark, Callable)

    assert hasattr(framework, 'parse')
    assert isinstance(framework.parse, Callable)

    return framework