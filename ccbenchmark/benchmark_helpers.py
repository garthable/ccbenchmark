import json
import sys
import subprocess
import re
import shutil
from pathlib import Path
import logging
from glob import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

from ccbenchmark.benchmark_data import BenchmarkData
from ccbenchmark.gui import show_gui
from ccbenchmark.util import strip_common_paths

def get_latest_mtime_in_dir(path: Path) -> float:
    """Gets time of modification in directory"""
    mtimes = [f.stat().st_mtime for f in path.rglob('*') if f.is_file()]
    return max(mtimes, default=path.stat().st_mtime)

def compare_benchmarks(benchmark_output_directory: Path, pattern: re.Pattern) -> None:
    """Compares benchmark results, launches gui"""

    in_iterations = set()
    iteration_paths = []
    for f in benchmark_output_directory.rglob('*'):
        if f.is_file() and f.parent not in in_iterations:
            iteration_paths.append(f.parent)
            in_iterations.add(f.parent)

    iteration_paths_sorted = sorted(
        iteration_paths,
        key=get_latest_mtime_in_dir
    )

    iteration_names = [path.name for path in iteration_paths_sorted]
    benchmark_data = BenchmarkData(iteration_names)

    for iteration_index, iteration_path in enumerate(iteration_paths_sorted):
        assert iteration_path.is_dir(), f'{iteration_path} is not a directory.'
        for json_file_path in iteration_path.iterdir():
            assert json_file_path.suffix == '.json', f'ERROR: None Json File: {json_file_path}'
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                try:
                    json_loaded = json.load(json_file)
                except json.JSONDecodeError as e:
                    logger.warning(f'Invalid JSON in {json_file_path}: {e}')
                    continue
                path = iteration_path.parent / json_file_path.name.split('.')[0]
                benchmark_data.add_json_file(iteration_index, json_loaded, path)
    
    benchmark_data.validate()
    benchmark_data.establish_common_time_unit()
    benchmark_data.strip_common_paths()
    show_gui(benchmark_data)

def run_single_benchmark(binary_path: Path, output_path: Path) -> int:
    """Runs a single benchmark binary and writes output to the given path."""
    cmd = [
        binary_path, 
        f'--benchmark_out={output_path}', 
        '--benchmark_out_format=json', 
        '--benchmark_report_aggregates_only=false'
    ]

    return subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=False)

def get_bin_paths(benchmark_root_dirs: list[Path]) -> list[Path]:
    binaries = []
    
    for benchmark_root_dir in benchmark_root_dirs:
        for path_str in glob(str(benchmark_root_dir)):
            path = Path(path_str)
            is_binary = shutil.which(path) is not None
            if is_binary and path.is_file():
                binaries.append(path)
    return binaries

def run_benchmarks(benchmark_root_dirs: list[Path], output_dir: Path, tag: str) -> None:
    """Runs all benchmarks in benchmark.txt"""
    binary_paths = get_bin_paths(benchmark_root_dirs)
    output_paths = [output_dir / stripped_path.parent / tag 
                    for stripped_path in strip_common_paths(binary_paths)]

    for binary_path, output_path in zip(binary_paths, output_paths):
        benchmark_name = binary_path.name
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f'Running benchmark: {benchmark_name}')

        result = run_single_benchmark(binary_path, output_path / f'{benchmark_name}.json')
        
        if result != 0:
            logger.warning(f'{benchmark_name}: Exited with code: {result}')
        else:
            logger.info(f'{benchmark_name}: OK')
        
        if tag != 'recent':
            recent_path = output_path.parent / 'recent'
            recent_path.mkdir(parents=True, exist_ok=True)
            dest_path = recent_path / f'{benchmark_name}.json'
            shutil.copy(output_path / f'{benchmark_name}.json', dest_path)
            # Updates mtime of file for freshness sorting.
            dest_path.touch()
            logger.debug(f"Copied result to recent: {dest_path}")

def init_benchmarks() -> None:
    pass