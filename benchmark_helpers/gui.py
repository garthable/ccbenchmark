import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import filedialog
import csv
from benchmark_helpers.benchmark_data import BenchmarkData, BenchmarkColumn, TimeType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_columns(is_aggregated: bool) -> list[str]:
    if not is_aggregated:
        return ['Iteration', 'Time', 'Time Delta (%)']  
    return ['Iteration', 'Mean Time', 'Mean Time Delta (%)', 
             'Median Time', 'Median Time Delta (%)', 'Standard Deviation', 
             'Standard Deviation Delta (%)', 'Coefficient of Variation (%)', 
             'Coefficient of Variation Delta (%)']

def create_benchmark_table(frame, benchmark_col: BenchmarkColumn, time_type=TimeType.REAL):
    """Generates data table"""
    tree = ttk.Treeview(frame)
    columns = get_columns(benchmark_col.aggregated)
    
    tree['columns'] = columns
    tree['show'] = 'headings'

    font = tkFont.Font()
    
    tree.tag_configure('evenrow', background='#f0f0ff')
    tree.tag_configure('oddrow', background='white')
    for i, benchmark_entry in enumerate(benchmark_col):
        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
        tree.insert('', 'end', values=benchmark_entry.get_row(benchmark_col.aggregated, time_type), tags=(tag,))

    for col in columns:
        max_width = font.measure(col)
        tree.heading(col, text=col)
        for item in tree.get_children():
            text = tree.set(item, col)
            max_width = max(max_width, font.measure(text))
        max_width += 20
        tree.column(col, minwidth=max_width, width=max_width, stretch=False, anchor='e')

    horizontal_scrollbar = ttk.Scrollbar(frame, command=tree.xview, orient='horizontal')
    horizontal_scrollbar.pack(side='bottom', fill='x')

    vertical_scrollbar = ttk.Scrollbar(frame, command=tree.yview, orient='vertical')
    vertical_scrollbar.pack(side='right', fill='y')

    tree.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)

    tree.pack(side='left', expand=True, fill='both')
    return tree

def show_gui(benchmark_data: BenchmarkData):
    """Displays gui for benchmark results"""
    root = tk.Tk()
    root.minsize(600, 400)
    root.title("Benchmark Results")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill='both')

    for benchmark_col, benchmark_name in zip(benchmark_data.matrix, benchmark_data.benchmark_names):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=benchmark_name)
        create_benchmark_table(tab, benchmark_col)

    selected_time_type = tk.StringVar(value='REAL')

    def update_tables():
        """Updates all benchmark tables with the selected time type."""
        time_type = TimeType[selected_time_type.get()]
        for i, tab in enumerate(notebook.tabs()):
            widget = notebook.nametowidget(tab)
            tree = widget.winfo_children()[0]

            benchmark_col = benchmark_data.matrix[i]
            for row_id, benchmark_entry in zip(tree.get_children(), benchmark_col):
                new_values = benchmark_entry.get_row(benchmark_col.aggregated, time_type)
                tree.item(row_id, values=new_values)

    radio_frame = ttk.Frame(root)
    ttk.Radiobutton(radio_frame, text="Real Time", variable=selected_time_type, value='REAL', command=update_tables).pack(side='left')
    ttk.Radiobutton(radio_frame, text="CPU Time", variable=selected_time_type, value='CPU', command=update_tables).pack(side='left')
    radio_frame.pack(fill='x')

    root.mainloop()