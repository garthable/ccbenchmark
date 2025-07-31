import tkinter as tk
import ttkbootstrap as ttk
import tkinter.font as tkFont
import logging
import sys

IMPORT_FAILURE_EXIT_CODE = 99

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from benchmark_helpers.benchmark_data import BenchmarkData, BenchmarkColumn, TimeType
except ImportError as e:
    logger.critical(f"Failed to import benchmark_data: {e}")
    sys.exit(IMPORT_FAILURE_EXIT_CODE)

def create_hierarchy(benchmark_data: BenchmarkData, parent: ttk.Frame) -> ttk.Treeview:
    created_paths = set()

    hierarchy = ttk.Treeview(parent)

    hierarchy.column("#0", minwidth=100, width=500, stretch=True)
    hierarchy.heading('#0', text='Benchmarks', anchor='w')

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

def get_columns(is_aggregated: bool) -> list[str]:
    if not is_aggregated:
        return ['Iteration', 'Time', 'Time Delta (%)']  
    return ['Iteration', 'Mean Time', 'Mean Time Delta (%)', 
             'Median Time', 'Median Time Delta (%)', 'Standard Deviation', 
             'Standard Deviation Delta (%)', 'Coefficient of Variation (%)', 
             'Coefficient of Variation Delta (%)']

def darken(hex_color, amount=10):
    hex_color = hex_color.lstrip("#")
    rgb = [max(0, int(hex_color[i:i+2], 16) - amount) for i in (0, 2, 4)]
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def create_benchmark_table(parent, benchmark_data: BenchmarkData, is_aggregated: bool):
    """Generates data table"""
    tree = ttk.Treeview(parent)
    columns = get_columns(is_aggregated)
    
    tree['columns'] = columns
    tree['show'] = 'headings'

    font = tkFont.Font()

    bg = style.lookup("Treeview", "background")
    even_bg = darken(bg, amount=10)
    odd_bg = darken(bg, amount=5)
    
    tree.tag_configure('evenrow', background=even_bg)
    tree.tag_configure('oddrow', background=odd_bg)
    for i in range(len(benchmark_data.iteration_names)):
        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
        tree.insert('', 'end', values=['' for i in range(len(columns))], tags=(tag,))

    for col in columns:
        max_width = font.measure(col)
        tree.heading(col, text=col)
        for item in tree.get_children():
            text = tree.set(item, col)
            max_width = max(max_width, font.measure(text))
        max_width += 20
        tree.column(col, minwidth=max_width, width=max_width, stretch=True, anchor='e')

    horizontal_scrollbar = ttk.Scrollbar(parent, command=tree.xview, orient='horizontal')
    horizontal_scrollbar.grid(row=1, column=0, sticky='ew')

    vertical_scrollbar = ttk.Scrollbar(parent, command=tree.yview, orient='vertical')
    vertical_scrollbar.grid(row=0, column=1, sticky='ns')

    tree.grid(row=0, column=0, sticky='nsew')

    tree.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
    return tree

def show_gui(benchmark_data: BenchmarkData):
    """Displays gui for benchmark results"""
    root = ttk.Window(themename='solar')
    root.minsize(600, 400)
    root.title("Benchmark Results")

    global style
    style = ttk.Style()

    horizontal_split = ttk.PanedWindow(root, orient='horizontal')
    horizontal_split.pack(fill='both', expand=True)

    left_frame = ttk.Frame(horizontal_split, width=200)
    horizontal_split.add(left_frame, weight=1)

    right_frame = ttk.Frame(horizontal_split)
    horizontal_split.add(right_frame, weight=4)

    right_frame.rowconfigure(0, weight=1)
    right_frame.columnconfigure(0, weight=1)
        
    hierarchy = create_hierarchy(benchmark_data, left_frame)
    table = create_benchmark_table(right_frame, benchmark_data, True)

    selected_index = 0

    def on_select(event):
        nonlocal selected_index
        selected_element = hierarchy.selection()
        if not selected_element:
            return
        element_id = selected_element[0]
        values = hierarchy.item(element_id, "values")
        if not values:
            return
        selected_index = int(values[0])
        update_tables()

    hierarchy.bind('<<TreeviewSelect>>', on_select)

    selected_time_type = tk.StringVar(value='REAL')

    def update_tables():
        time_type = TimeType[selected_time_type.get()]
        benchmark_col = benchmark_data.matrix[selected_index]

        headings = get_columns(benchmark_col.aggregated)
        all_cols = table["columns"]

        for i, col_id in enumerate(all_cols):
            heading = headings[i] if i < len(headings) else ""
            table.heading(col_id, text=heading)

        for row_id, benchmark_entry in zip(table.get_children(), benchmark_col):
            row_values = benchmark_entry.get_row(benchmark_col.aggregated, time_type)
            padded = row_values + [""] * (len(all_cols) - len(row_values))
            table.item(row_id, values=padded)

    update_tables()

    radio_frame = ttk.Frame(root)
    ttk.Radiobutton(radio_frame, text="Real Time", variable=selected_time_type, value='REAL', command=update_tables).pack(side='left')
    ttk.Radiobutton(radio_frame, text="CPU Time", variable=selected_time_type, value='CPU', command=update_tables).pack(side='left')
    radio_frame.pack(fill='x')

    root.mainloop()