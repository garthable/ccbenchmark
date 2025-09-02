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
import ccbenchmark.benchmark_framework as framework
import ccbenchmark.benchmark_settings as settings

def get_latest_mtime_in_dir(path: Path) -> float:
    """Gets time of modification in directory"""
    mtimes = [f.stat().st_mtime for f in path.rglob('*') if f.is_file()]
    return max(mtimes, default=path.stat().st_mtime)

def compare_benchmarks(benchmark_output_directory: Path, pattern: re.Pattern) -> None:
    """Compares benchmark results, launches gui"""

    in_iterations = set()
    iteration_paths: list[Path] = []
    for f in benchmark_output_directory.rglob('*'):
        if not (f.is_file() and f.parent is not None and f.parent not in in_iterations):
            continue
        if not (len(str(f.parent.name)) >= len('_iter_') and str(f.parent.name)[0:len('_iter_')] == '_iter_'):
            continue
        iteration_paths.append(f.parent)
        in_iterations.add(f.parent)

    iteration_paths_sorted = sorted(
        iteration_paths,
        key=get_latest_mtime_in_dir
    )

    in_iteration_names = set()
    iteration_names_to_index: dict[str, int] = {}
    for path in iteration_paths_sorted:
        name = path.name[len('_iter_'):]
        if name in in_iteration_names:
            continue
        in_iteration_names.add(name)
        iteration_names_to_index[name] = len(iteration_names_to_index)

    benchmark_data = BenchmarkData(list(iteration_names_to_index.keys()))

    for iteration_path in iteration_paths_sorted:
        name = iteration_path.name[len('_iter_'):]
        iteration_index = iteration_names_to_index[name]
        assert iteration_path.is_dir(), f'{iteration_path} is not a directory.'
        for file_path in iteration_path.iterdir():
            with open(file_path, 'r', encoding='locale') as file_stream:
                benchmark_path = iteration_path.parent / file_path.name.split('.')[0]
                benchmark_data.add_file(iteration_index, file_stream, file_path, benchmark_path)
    
    benchmark_data.validate()
    benchmark_data.establish_common_time_unit()
    benchmark_data.strip_common_paths()
    show_gui(benchmark_data)

def get_runnable_paths(benchmark_root_dirs: list[Path]) -> list[Path]:
    runnables = []
    
    for benchmark_root_dir in benchmark_root_dirs:
        for path_str in glob(str(benchmark_root_dir)):
            path = Path(path_str)
            if path.is_file():
                runnables.append(path)
    return runnables

def remove_similiar_files(dir: Path, file_name: Path) -> None:
    for path in dir.glob(f'{str(file_name.with_suffix(''))}.*'):
        if path.suffix == file_name.suffix:
            continue
        path.unlink(missing_ok=True)

def run_benchmarks(benchmark_root_dirs: list[Path], output_dir: Path, tag: str) -> None:
    """Runs all benchmarks in benchmark.txt"""
    runnable_paths = get_runnable_paths(benchmark_root_dirs)
    output_paths = [output_dir / stripped_path.parent / f'_iter_{tag}' 
                    for stripped_path in strip_common_paths(runnable_paths)]

    for runnable_path, output_path in zip(runnable_paths, output_paths):
        benchmark_name = runnable_path.with_suffix('').name
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f'Running benchmark: {benchmark_name}')

        file_name = Path(f'{benchmark_name}.{settings.local_settings.output_format}')
        output_location = output_path / file_name

        result = framework.framework.run_single_benchmark(runnable_path, output_location)
        remove_similiar_files(output_path, file_name)
        
        if result != 0:
            logger.warning(f'{benchmark_name}: Exited with code: {result}')
        else:
            logger.info(f'{benchmark_name}: OK')
        
        if tag != 'recent':
            recent_path = output_path.parent / '_iter_recent'
            recent_path.mkdir(parents=True, exist_ok=True)
            dest_path = recent_path / file_name
            shutil.copy(output_location, dest_path)
            remove_similiar_files(recent_path, file_name)
            # Updates mtime of file for freshness sorting.
            dest_path.touch()
            logger.debug(f"Copied result to recent: {dest_path}")

def init_benchmarks() -> None:
    pass