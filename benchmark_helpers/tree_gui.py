import tkinter as tk
from tkinter import ttk
from pathlib import Path
import logging
import sys

IMPORT_FAILURE_EXIT_CODE = 99

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from benchmark_helpers.benchmark_data import BenchmarkData, BenchmarkColumn, BenchmarkEntry, BenchmarkTime
except ImportError as e:
    logger.critical(f"Failed to import benchmark_data: {e}")
    sys.exit(IMPORT_FAILURE_EXIT_CODE)

def create_hierarchy(benchmark_data: BenchmarkData, parent: ttk.Frame) -> ttk.Treeview:
    created_paths = set()

    hierarchy = ttk.Treeview(parent)

    for i, (col, benchmark_name) in enumerate(zip(benchmark_data.matrix, benchmark_data.benchmark_names)):
        prev = ''
        for part in col.benchmark_bin_path.parts:
            segment = f'{prev}/{part}'
            if segment not in created_paths:
                hierarchy.insert(str(prev), len(created_paths), str(segment), text=part)
                created_paths.add(segment)
            prev = segment
        segment = f'{prev}/{benchmark_name}'
        if segment not in created_paths:
            hierarchy.insert(str(prev), len(created_paths), str(segment), text=benchmark_name, values=(i))
            created_paths.add(segment)

    hierarchy.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(hierarchy, command=hierarchy.xview, orient='vertical')
    scrollbar.pack(side='right', fill='y')

    hierarchy.configure(yscrollcommand=scrollbar.set)

    return hierarchy