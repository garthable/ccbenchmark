import importlib
from ccbenchmark.frameworks.util.parse_result import ParseResult
from typing import cast, Protocol, Generator, Callable
from pathlib import Path
from io import TextIOWrapper

class Framework(Protocol):
    SUPPORTED_FORMATS: set[str]

    run_single_benchmark: Callable[[Path, Path, str], int]
    parse: Callable[[TextIOWrapper, Path], Generator[ParseResult, None, None]]

def import_framework(framework_name: str, output_format: str) -> Framework:
    framework = cast(Framework, importlib.import_module(f'ccbenchmark.frameworks.{framework_name}'))

    assert hasattr(framework, 'SUPPORTED_FORMATS')
    assert isinstance(framework.SUPPORTED_FORMATS, set)

    assert output_format in framework.SUPPORTED_FORMATS

    assert hasattr(framework, 'run_single_benchmark')
    assert isinstance(framework.run_single_benchmark, Callable)

    assert hasattr(framework, 'parse')
    assert isinstance(framework.parse, Callable)

    return framework