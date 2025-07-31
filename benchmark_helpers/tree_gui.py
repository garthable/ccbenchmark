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

import tkinter.font as tkFont

def create_hierarchy(benchmark_data: BenchmarkData, parent: ttk.Frame) -> ttk.Treeview:
    created_paths = set()

    hierarchy = ttk.Treeview(parent)

    hierarchy.column("#0", minwidth=500, width=500, stretch=True)

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

    hierarchy.update_idletasks()
    hierarchy.event_generate("<Configure>")

    hierarchy.grid(row=0, column=1, sticky='nsew')

    v_scrollbar = ttk.Scrollbar(parent, command=hierarchy.yview, orient='vertical')
    v_scrollbar.grid(row=0, column=0, sticky='ns')

    h_scrollbar = ttk.Scrollbar(parent, command=hierarchy.xview, orient='horizontal')
    h_scrollbar.grid(row=1, column=1, sticky='ew')

    hierarchy.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    parent.columnconfigure(1, weight=1)
    parent.rowconfigure(0, weight=1)

    return hierarchy