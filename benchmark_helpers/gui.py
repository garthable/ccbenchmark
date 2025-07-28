import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from benchmark_helpers.benchmark_data import *

def create_table_gui(frame, benchmark_col: BenchmarkColumn, time_type=TimeType.REAL_TIME_INDEX):
    tree = ttk.Treeview(frame)
    if not benchmark_col.aggregated:
        columns = ['Iteration', 'Time', 'Time Delta (%)']  
    else: 
        columns = ['Iteration', 'Mean Time', 'Mean Time Delta (%)', 
                   'Median Time', 'Median Time Delta (%)', 'Standard Deviation', 
                   'Standard Deviation Delta (%)', 'Coefficient of Variation (%)', 
                   'Coefficient of Variation Delta (%)']
    
    tree['columns'] = columns
    tree['show'] = 'headings'

    font = tkFont.Font()
    
    for benchmark_entry in benchmark_col:
        tree.insert('', 'end', values=benchmark_entry.get_row(benchmark_col.aggregated, time_type))

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

def show_gui(benchmark_data: BenchmarkData):
    root = tk.Tk()
    root.title("Benchmark Results")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill='both')

    for benchmark_col, benchmark_name in zip(benchmark_data.matrix, benchmark_data.benchmark_names):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=benchmark_name)
        create_table_gui(tab, benchmark_col)

    root.mainloop()