import shutil
from pathlib import Path
import logging
from glob import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

from ccbenchmark.benchmark_data import load_benchmark_data
from ccbenchmark.gui import show_gui
from ccbenchmark.util import strip_common_paths
from ccbenchmark.benchmark_framework import Framework

def get_latest_mtime_in_dir(path_and_framework: tuple[Path, Framework]) -> float:
    """Gets time of modification in directory
    Args:
        Tuple of path, and framework used (framework is ignored).
    Returns:
        Latest time of file modified within the directory.
    """
    path = path_and_framework[0]
    mtimes = [f.stat().st_mtime for f in path.rglob('*') if f.is_file()]
    return max(mtimes, default=path.stat().st_mtime)

def get_iteration_paths(output_directories: list[Path], frameworks: list[Framework]) -> list[Path]:
    in_iterations = set()
    iteration_paths: list[Path] = []
    for output_directory, framework in zip(output_directories, frameworks):
        for f in output_directory.rglob('*'):
            if not (f.is_file() and f.parent is not None and f.parent not in in_iterations):
                continue
            if not (len(str(f.parent.name)) >= len('_iter_') and str(f.parent.name)[0:len('_iter_')] == '_iter_'):
                continue
            iteration_paths.append((f.parent, framework))
            in_iterations.add(f.parent)

    return sorted(
        iteration_paths,
        key=get_latest_mtime_in_dir
    )

def get_iteration_names_to_index(iteration_paths: list[tuple[Path, Framework]]) -> dict[str, int]:
    in_iteration_names = set()
    iteration_names_to_index: dict[str, int] = {}
    for path, _ in iteration_paths:
        name = path.name[len('_iter_'):]
        if name in in_iteration_names:
            continue
        in_iteration_names.add(name)
        iteration_names_to_index[name] = len(iteration_names_to_index)
    return iteration_names_to_index

def compare_benchmarks(benchmark_output_directory_list: list[Path], frameworks: list[Framework]) -> None:
    """Compares benchmark results, launches gui"""

    iteration_paths_and_frameworks = get_iteration_paths(benchmark_output_directory_list, frameworks)
    iteration_names_to_index = get_iteration_names_to_index(iteration_paths_and_frameworks)

    benchmark_data = load_benchmark_data(iteration_names_to_index, iteration_paths_and_frameworks)
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

def run_benchmarks(runnables_list: list[Path], output_dir: Path, framework: Framework, output_format: str, tag: str) -> None:
    """Runs all benchmarks in benchmark.txt"""
    runnable_paths = get_runnable_paths(runnables_list)
    output_paths = [output_dir / stripped_path.parent / f'_iter_{tag}' 
                    for stripped_path in strip_common_paths(runnable_paths)]

    for runnable_path, output_path in zip(runnable_paths, output_paths):
        benchmark_name = runnable_path.with_suffix('').name
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f'Running benchmark: {benchmark_name}')

        file_name = Path(f'{benchmark_name}.{output_format}')
        output_location = output_path / file_name

        result = framework.run_single_benchmark(runnable_path, output_location, output_format)
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
