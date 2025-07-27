import json
import subprocess
import argparse
from pathlib import Path
import re
import shutil
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import os

def create_table_gui(benchmark_names, iteration_names, matrix, frame, use_cpu_time):
    tree = ttk.Treeview(frame)

    columns = [''] + benchmark_names
    tree['columns'] = columns
    tree['show'] = 'headings'

    font = tkFont.Font()

    for iter_name, row in zip(iteration_names, matrix):
        formatted_row = [f'{v[0][use_cpu_time]:.2f} {v[1]}' if isinstance(v, tuple) else "N/A" for v in row]
        tree.insert('', 'end', values=[iter_name] + formatted_row)

    for col in columns:
        max_width = font.measure(col)
        tree.heading(col, text=col)
        for item in tree.get_children():
            text = tree.set(item, col)
            max_width = max(max_width, font.measure(text))
        max_width += 20
        tree.column(col, minwidth=max_width, width=max_width, stretch=False, anchor='center')

    horizontal_scrollbar = ttk.Scrollbar(frame, command=tree.xview, orient='horizontal')
    horizontal_scrollbar.pack(side='bottom', fill='x')

    verticle_scrollbar = ttk.Scrollbar(frame, command=tree.yview, orient='vertical')
    verticle_scrollbar.pack(side='right', fill='y')

    tree.configure(yscrollcommand=verticle_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)

    tree.pack(side='left', expand=False, fill='both')
    return tree

def show_gui(benchmark_names, iteration_names, matrix):
    root = tk.Tk()
    root.title("Benchmark Results")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill='both')

    # for benchmark_name in benchmark_names:
    #     tab = ttk.Frame(notebook)
    #     notebook.add(tab, text=benchmark_name)
    #     create_table_gui()

    # Create a frame to serve as the tab content container
    real_time_table_tab = ttk.Frame(notebook)
    notebook.add(real_time_table_tab, text="Real Time (Table)")
    cpu_time_table_tab = ttk.Frame(notebook)
    notebook.add(cpu_time_table_tab, text="Cpu Time (Table)")

    create_table_gui(benchmark_names, iteration_names, matrix, real_time_table_tab, use_cpu_time=False)
    create_table_gui(benchmark_names, iteration_names, matrix, cpu_time_table_tab, use_cpu_time=True)

    root.mainloop()

def get_latest_mtime_in_dir(path: Path) -> float:
    mtimes = [f.stat().st_mtime for f in path.rglob('*') if f.is_file()]
    return max(mtimes, default=path.stat().st_mtime)

def init_benchmark_names(benchmark_re_name, benchmark_result_folder) -> list:
    benchmark_re = re.compile(benchmark_re_name)
    current_benchmark_folder = benchmark_result_folder / 'recent'
    benchmark_names = []
    for json_file_path in current_benchmark_folder.iterdir():
        with open(json_file_path, 'r') as json_file:
            json_loaded = json.load(json_file)
            for benchmark in json_loaded['benchmarks']:
                name = benchmark['name']
                if not benchmark_re.search(name):
                    continue
                benchmark_names.append(name)
    return benchmark_names

def compare_benchmarks(benchmark_folder: Path, benchmark_re_name: str):
    benchmark_result_folder = benchmark_folder.parent / 'benchmark_results'

    benchmark_names = init_benchmark_names(benchmark_re_name, benchmark_result_folder)

    iteration_paths_sorted = sorted(
        (f for f in benchmark_result_folder.iterdir() if f.is_dir()),
        key=get_latest_mtime_in_dir
    )

    iteration_names = [None]*len(iteration_paths_sorted)
    matrix = [[None] * len(benchmark_names) for _ in range(len(iteration_paths_sorted))]

    for i, iteration_path in enumerate(iteration_paths_sorted):
        iteration_names[i] = iteration_path.name

        for json_file_path in iteration_path.iterdir():
            with open(json_file_path, 'r') as json_file:
                json_loaded = json.load(json_file)
                for benchmark in json_loaded['benchmarks']:
                    name = benchmark['name']
                    try:
                        j = benchmark_names.index(name)
                        matrix[i][j] = ((benchmark['real_time'], benchmark['cpu_time']), benchmark['time_unit'])
                    
                    except ValueError:
                        continue

    show_gui(benchmark_names, iteration_names, matrix)

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