import json
import sys
import subprocess
import re
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMPORT_FAILURE_EXIT_CODE = 99

try:
    from benchmark_helpers.benchmark_data import BenchmarkData
except ImportError as e:
    logger.critical(f"Failed to import benchmark_data: {e}")
    sys.exit(IMPORT_FAILURE_EXIT_CODE)
try:
    from benchmark_helpers.gui import show_gui
except ImportError as e:
    logger.critical(f"Failed to import gui: {e}")
    sys.exit(IMPORT_FAILURE_EXIT_CODE)

def get_latest_mtime_in_dir(path: Path) -> float:
    """Gets time of modification in directory"""
    mtimes = [f.stat().st_mtime for f in path.rglob('*') if f.is_file()]
    return max(mtimes, default=path.stat().st_mtime)

def init_benchmark_names(pattern: re.Pattern, benchmark_result_folder: Path) -> tuple[list[str], dict[str, int]]:
    """Gets names of benchmarks from recent folder"""
    current_benchmark_folder = benchmark_result_folder / 'recent'

    benchmark_names_set = set()

    benchmark_names = []
    benchmark_name_to_index = {}

    for json_file_path in current_benchmark_folder.iterdir():
        if not json_file_path.suffix == '.json':
            continue
        if not json_file_path.is_file():
            logger.warning(f"Skipping non-file: {json_file_path}")
            continue
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            json_loaded = json.load(json_file)
            try:
                benchmarks = json_loaded['benchmarks']
            except KeyError:
                logger.warning(f"Missing 'benchmarks' key in {json_file_path}")
                continue
            for benchmark in benchmarks:
                try:
                    name = benchmark['run_name']
                except KeyError:
                    logger.warning(f"Missing 'run_name' key in {json_file_path}")
                    continue
                if not pattern.search(name) or name in benchmark_names_set:
                    continue
                benchmark_names_set.add(name)
                benchmark_names.append(name)
                benchmark_name_to_index[name] = len(benchmark_names) - 1

    return benchmark_names, benchmark_name_to_index

def compare_benchmarks(benchmark_folder: Path, pattern: re.Pattern) -> None:
    """Compares benchmark results, launches gui"""
    benchmark_result_folder = benchmark_folder.parent / 'benchmark_results'

    iteration_paths_sorted = sorted(
        (f for f in benchmark_result_folder.iterdir() if f.is_dir()),
        key=get_latest_mtime_in_dir
    )

    iteration_names = [path.name for path in iteration_paths_sorted]
    benchmark_names, benchmark_name_to_index = init_benchmark_names(pattern, benchmark_result_folder)
    benchmark_data = BenchmarkData(benchmark_names, iteration_names)

    for iteration_index, iteration_path in enumerate(iteration_paths_sorted):
        for json_file_path in iteration_path.iterdir():
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                try:
                    json_loaded = json.load(json_file)
                except json.JSONDecodeError as e:
                    logger.warning(f'Invalid JSON in {json_file_path}: {e}')
                    continue
                benchmark_data.add_json_file(iteration_index, json_loaded, benchmark_name_to_index)
    benchmark_data.compute_delta()
    show_gui(benchmark_data)

def init_dir(benchmark_path: Path, tag: str) -> Path:
    """Initializes directory, prevents errors from directory not existing"""
    output_dir = benchmark_path.parent / 'benchmark_results' / tag
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f'Failed to create directory {output_dir}: {e}')

    return output_dir

def run_single_benchmark(binary_path: Path, output_path: Path) -> int:
    """Runs a single benchmark binary and writes output to the given path."""
    cmd = [
        binary_path, 
        f'--benchmark_out={output_path}', 
        '--benchmark_out_format=json', 
        '--benchmark_report_aggregates_only=false'
    ]

    return subprocess.call(cmd, stdin=None, stdout=None, stderr=None, shell=False)
    
def run_benchmarks(benchmark_path: Path, tag: str) -> None:
    """Runs all benchmarks in benchmark.txt"""
    output_dir = init_dir(benchmark_path, tag)
    if tag != 'recent':
        recent_dir = init_dir(benchmark_path, 'recent')

    with open(benchmark_path, 'r', encoding='utf-8') as benchmark_file:
        for line in benchmark_file:
            line = line.strip()
            if not line:
                logger.warning("Skipping empty line in benchmark file.")
                continue
            binary_path = Path(line)
            benchmark_name = binary_path.name

            if not binary_path.is_file():
                logger.warning(f"Benchmark binary not found: {binary_path}")
                continue

            logger.info(f'Running benchmark: {benchmark_name}')

            result = run_single_benchmark(binary_path, output_dir / f'{benchmark_name}.json')
            
            if result != 0:
                logger.warning(f'{benchmark_name}: Exited with code: {result}')
            else:
                logger.info(f'{benchmark_name}: OK')
            
            if tag != 'recent':
                dest_path = recent_dir / f'{benchmark_name}.json'
                shutil.copy(output_dir / f'{benchmark_name}.json', dest_path)
                # Updates mtime of file for freshness sorting.
                dest_path.touch()
                logger.debug(f"Copied result to recent: {dest_path}")