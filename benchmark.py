import json
import subprocess
import argparse
from pathlib import Path
import re
import shutil
import os
from benchmark_helpers.gui import show_gui
from benchmark_helpers.benchmark_data import *

def get_latest_mtime_in_dir(path: Path) -> float:
    mtimes = [f.stat().st_mtime for f in path.rglob('*') if f.is_file()]
    return max(mtimes, default=path.stat().st_mtime)

def init_benchmark_names(benchmark_re_name, benchmark_result_folder) -> list:
    benchmark_re = re.compile(benchmark_re_name)
    current_benchmark_folder = benchmark_result_folder / 'recent'

    benchmark_names_set = set()

    benchmark_names = []
    benchmark_name_to_index = {}

    for json_file_path in current_benchmark_folder.iterdir():
        with open(json_file_path, 'r') as json_file:
            json_loaded = json.load(json_file)
            for benchmark in json_loaded['benchmarks']:
                name = benchmark['run_name']
                if not benchmark_re.search(name) or name in benchmark_names_set:
                    continue
                benchmark_names_set.add(name)
                benchmark_names.append(name)
                benchmark_name_to_index[name] = len(benchmark_names) - 1

    return benchmark_names, benchmark_name_to_index

def compare_benchmarks(benchmark_folder: Path, benchmark_re_name: str):
    benchmark_result_folder = benchmark_folder.parent / 'benchmark_results'

    iteration_paths_sorted = sorted(
        (f for f in benchmark_result_folder.iterdir() if f.is_dir()),
        key=get_latest_mtime_in_dir
    )

    iteration_names = [path.name for path in iteration_paths_sorted]
    benchmark_names, benchmark_name_to_index = init_benchmark_names(benchmark_re_name, benchmark_result_folder)
    benchmark_data = BenchmarkData(benchmark_names, iteration_names)

    for iteration_index, iteration_path in enumerate(iteration_paths_sorted):
        for json_file_path in iteration_path.iterdir():
            with open(json_file_path, 'r') as json_file:
                json_loaded = json.load(json_file)
                benchmark_data.add_json_file(iteration_index, json_loaded, benchmark_name_to_index)
    benchmark_data.compute_delta()
    show_gui(benchmark_data)

def init_dir(benchmark_path: Path, tag: str):
    dir = benchmark_path.parent
    output_dir = dir / 'benchmark_results'

    result = subprocess.call(['mkdir', output_dir], stdin=None, stdout=None, stderr=None, shell=False)
    if result != 0:
        print(f'Failed to create {f'benchmark_results/'}')

    output_dir = output_dir / tag
    result = subprocess.call(['mkdir', output_dir], stdin=None, stdout=None, stderr=None, shell=False)
    if result != 0:
        print(f'Failed to create {f'benchmark_results/{tag}/'}')
    return output_dir

def run_benchmarks(benchmark_path: Path, tag: str):
    output_dir = init_dir(benchmark_path, tag)
    if tag != 'recent':
        recent_dir = init_dir(benchmark_path, 'recent')

    with open(benchmark_path, 'r') as benchmark_file:
        for line in benchmark_file:
            line = line.strip()
            benchmark_name = Path(line).name
            result = subprocess.call([
                line, 
                f'--benchmark_out={output_dir}/{benchmark_name}.json', 
                '--benchmark_out_format=json', 
                '--benchmark_report_aggregates_only=false'], 
                stdin=None, stdout=None, stderr=None, shell=False)
            if result != 0:
                print(f'{benchmark_name}: Exited with code: {result}')
            else:
                print(f'{benchmark_name}: OK')
            
            if tag != 'recent':
                shutil.copy(f'{output_dir}/{benchmark_name}.json', f'{recent_dir}')
                os.utime(f'{recent_dir}/{benchmark_name}.json', None)

def main(args):
    working_dir = Path(args.working_directory)
    benchmark_path = working_dir / 'benchmarks.txt'
    if args.action in {'run', 'r', 'run_and_compare', 'rac'}:
        run_benchmarks(benchmark_path, args.tag)
    if args.action in {'compare', 'c', 'run_and_compare', 'rac'}:
        compare_benchmarks(benchmark_path, args.compare_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='benchmark'
    )

    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    run_parser = subparsers.add_parser('run', aliases=['r'])
    run_parser.add_argument('tag', nargs='?', default='recent')

    compare_parser = subparsers.add_parser('compare', aliases=['c'])
    compare_parser.add_argument('compare_name', nargs='?', default='.*')

    run_and_compare_parser = subparsers.add_parser('run_and_compare', aliases=['rac'])
    run_and_compare_parser.add_argument('tag', nargs='?', default='recent')
    run_and_compare_parser.add_argument('compare_name', nargs='?', default='.*')

    parser.add_argument('-w', '--working_directory', nargs='?', default='')

    args = parser.parse_args()

    main(args)