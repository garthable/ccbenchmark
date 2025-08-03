from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore
import sys
from pathlib import Path
from enum import IntEnum

from benchmark_helpers.benchmark_data import BenchmarkColumn, BenchmarkData, BenchmarkEntry, TimeType
from benchmark_helpers.util import time_to_str

def get_columns(selected_column_indices: list[int], benchmark_data: BenchmarkData) -> list[str]:
    if len(selected_column_indices) == 0:
        return []
    
    aggregated = False
    for index in selected_column_indices:
        aggregated = aggregated or benchmark_data.matrix[index].aggregated

    if not aggregated:
        columns = [['Time', 'Time Δ (%)']]
    else:
        columns = [['Mean Time', 'Mean Time Δ (%)'], 
                   ['Median Time', 'Median Time Δ (%)'], 
                   ['Standard Deviation', 'Standard Deviation Δ (%)'], 
                   ['Coefficient of Variation (%)', 'Coefficient of Variation Δ (%)']]

    for i, _ in enumerate(columns):
        assert len(columns[i]), f'Column contains nothing!'
        col_name = columns[i][0]
        for j in selected_column_indices[1:]:
            benchmark_name = benchmark_data.benchmark_names[j]
            columns[i].append(f'{col_name} {benchmark_name} Δ (%)')

    flat_list = [
        value
        for col in columns
        for value in col
    ]
    return flat_list

def column_to_str_matrix(selected_column_indices: list[int], benchmark_data: BenchmarkData, time_type: TimeType) -> list[list[str]]:
    aggregated = False
    for index in selected_column_indices:
        aggregated = aggregated or benchmark_data.matrix[index].aggregated

    matrix: list[list[list[str]]] = []
    if len(selected_column_indices) == 0:
        return []
    main_index = selected_column_indices[0]
    main_column = benchmark_data.matrix[main_index]
    for entry in main_column:
        row = entry.get_row(main_column.aggregated, time_type)
        matrix.append(row)

    for i in selected_column_indices[1:]:
        other_column = benchmark_data.matrix[i]
        for j, (other_entry, main_entry) in enumerate(zip(other_column, main_column)):
            if aggregated:
                other_times = [other_entry.mean_time, other_entry.median_time, other_entry.stddev_time, other_entry.cv_time]
                main_times = [main_entry.mean_time, main_entry.median_time, main_entry.stddev_time, main_entry.cv_time]
            else:
                other_times = [other_entry.time]
                main_times = [main_entry.time]
            for k, (other_time, main_time) in enumerate(zip(other_times, main_times)):
                other_value = other_time.times[time_type]
                main_value = main_time.times[time_type]

                if j >= len(matrix) or k >= len(matrix[j]):
                    continue

                if other_value is None or main_value is None or main_value == 0:
                    matrix[j][k].append('N/A')
                    continue

                comparison = ((other_value - main_value) / main_value) * 100.0
                matrix[j][k].append(time_to_str(comparison, '%'))
    flattened_matrix: list[list[str]] = []
    for column in matrix:
        new_row = [
            value
            for col in column
            for value in col
        ]
        flattened_matrix.append(new_row)
    return flattened_matrix

def data_to_dict(benchmark_data: BenchmarkData) -> dict:
    data_dict = {}
    for i, (col, benchmark_name) in enumerate(zip(benchmark_data.matrix, benchmark_data.benchmark_names)):
        current_dict = data_dict
        for part in col.benchmark_bin_path.parts:
            next_dict: dict | None = data_dict.get(part)
            if next_dict is None:
                current_dict[part] = {}
                next_dict = current_dict[part]
            current_dict = next_dict
        current_dict[benchmark_name] = i
    return data_dict

class StickyMenu(QMenu):
    def mouseReleaseEvent(self, event):
        action = self.actionAt(event.pos())
        if action and action.isCheckable():
            action.setChecked(not action.isChecked())
        else:
            super().mouseReleaseEvent(event)

class DropdownChecks(QToolButton):
    def __init__(self, text: str, toolbar: QToolBar, main_window: QMainWindow):
        super().__init__()
        self.setMenu(StickyMenu())
        self.setText(text)
        self.setPopupMode(QToolButton.InstantPopup)
        self.main_window = main_window
        toolbar.addWidget(self)

    def addAction(self, text: str, checkable: bool, func, already_checked: bool = False, data: dict = {}) -> 'DropdownChecks':
        action = QAction(text, self.main_window, checkable=checkable)
        action.setChecked(already_checked)
        action.setData(data)
        self.menu().addAction(action)
        if func:
            action.toggled.connect(func)
        return self

class DropdownSelect(QToolButton):
    def __init__(self, toolbar: QToolBar, main_window: QMainWindow):
        super().__init__()
        self.setMenu(QMenu())
        self.setText(None)
        self.setPopupMode(QToolButton.InstantPopup)
        self.main_window = main_window
        self._group = QActionGroup(main_window)
        self._group.setExclusive(True)
        toolbar.addWidget(self)

    def addAction(self, text: str, func=None) -> 'DropdownSelect':
        assert type(text) is str, f"'{text}' is not a str. {type(text)}"
        action = QAction(text, self.main_window)
        action.setCheckable(True)
        self.menu().addAction(action)

        self._group.addAction(action)

        if self.text() == '':
            self.setText(text)
            action.setChecked(True)

        def select_button():
            sender_action: QAction = self.main_window.sender()
            self.setText(sender_action.text())
            sender_action.setChecked(True)

        action.triggered.connect(select_button)
        if func is not None:
            action.triggered.connect(func)
        return self

class MainWindow(QMainWindow):
    def __init__(self, benchmark_data: BenchmarkData):
        super().__init__()
        self.benchmark_data = benchmark_data
        self.time_type = TimeType.REAL

        self.selected_indicies: list[int] = []
        assert len(benchmark_data.benchmark_names) != 0, f'no benchmark names!'
        self.selected_names: list[str] = []

        self.table = self.init_table()
        self.tree = self.init_tree()
        self.toolbar = self.init_toolbar()
        self.selmodel = self.init_selmodel()
        
        self.selmodel.selectionChanged.connect(self.selection_change)

        self.splitter = QSplitter()

        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.table)

        self.setCentralWidget(self.splitter)

        QTimer.singleShot(0, self.set_split_sizes)

    def init_table(self) -> QTableWidget:
        self.table = QTableWidget()
        column_names = get_columns(self.selected_indicies, self.benchmark_data)
        row_names = self.benchmark_data.iteration_names
        table_data = column_to_str_matrix(self.selected_indicies, self.benchmark_data, self.time_type)
        self.modify_table(column_names, row_names, table_data)
        return self.table

    def init_toolbar(self) -> QToolBar:
        self.toolbar = QToolBar('Main Toolbar')
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        column_names = get_columns(self.selected_indicies, self.benchmark_data)
        self.modify_toolbar(column_names, self.selected_names)
        return self.toolbar

    def init_tree(self) -> QTreeWidget:
        self.tree = QTreeWidget()
        self.tree.model().setHeaderData(0, QtCore.Qt.Horizontal, 'Benchmarks')
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        data = data_to_dict(self.benchmark_data)
        self.build_tree(self.tree, data)
        return self.tree
    
    def init_selmodel(self) -> QtCore.QItemSelectionModel:
        return self.tree.selectionModel()

    def modify_table(self, columns_names: list[str], row_names: list[str], table_data: list[list[str]]):
        min_column_count = 20
        min_row_count = 35

        input_column_count = len(columns_names)
        input_row_count = len(row_names)

        column_count = max(input_column_count, min_column_count)
        row_count = max(input_row_count, min_row_count)

        additional_column_names = [''] * max(min_column_count - input_column_count, 0)
        additional_row_names = [''] * max(min_row_count - input_row_count, 0)

        self.table.setColumnCount(column_count)
        self.table.setRowCount(row_count)
        
        self.table.setHorizontalHeaderLabels(columns_names + additional_column_names)
        self.table.setVerticalHeaderLabels(row_names + additional_row_names)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        for i in range(column_count):
            self.table.showColumn(i)
            for j in range(row_count):
                if len(table_data) != 0 and i < len(table_data[0]) and j < len(table_data):
                    text = table_data[j][i]
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(j, i, item)
                else:
                    item = QTableWidgetItem('')
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(j, i, item)
        self.table.resizeColumnsToContents()

    def modify_toolbar(self, columns: list[str], selected_benchmarks: list[str]):
        self.toolbar.clear()
        show_stats_menu = DropdownChecks('Shown Stats', self.toolbar, self)

        def toggle_cpu_real_time():
            action: QAction = self.sender()
            if action.text() == 'Real Time':
                self.time_type = TimeType.REAL
            elif action.text() == 'CPU Time':
                self.time_type = TimeType.CPU
            column_names = get_columns(self.selected_indicies, self.benchmark_data)
            row_names = self.benchmark_data.iteration_names
            table_data = column_to_str_matrix(self.selected_indicies, self.benchmark_data, self.time_type)
            
            self.modify_table(column_names, row_names, table_data)
        
        def toggle_column():
            action: QAction = self.sender()
            data: dict = action.data()
            i = data.get('column_index')
            if i is not None:
                if not self.table.isColumnHidden(i):
                    self.table.hideColumn(i)
                else:
                    self.table.showColumn(i)

        for i, col in enumerate(columns):
            show_stats_menu.addAction(col, True, toggle_column, True, data={'column_index': i})

        DropdownSelect(self.toolbar, self)\
            .addAction('Real Time', toggle_cpu_real_time)\
            .addAction('CPU Time', toggle_cpu_real_time)
        
        main_benchmark_menu = DropdownSelect(self.toolbar, self)
        for selected_benchmark in selected_benchmarks:
            main_benchmark_menu.addAction(selected_benchmark, self.change_parent_selected)

    def change_parent_selected(self):
        action: QAction = self.sender()
        name = action.text()
        try:
            index = self.selected_names.index(name)
        except ValueError:
            return
        self.selected_names.insert(0, self.selected_names.pop(index))
        self.selected_indicies.insert(0, self.selected_indicies.pop(index))

        column_names = get_columns(self.selected_indicies, self.benchmark_data)
        row_names = self.benchmark_data.iteration_names
        table_data = column_to_str_matrix(self.selected_indicies, self.benchmark_data, self.time_type)

        self.modify_table(column_names, row_names, table_data)

    def build_tree(self, parent: QTreeWidget, data: dict):
        for key, value in data.items():
            item = QTreeWidgetItem(parent)
            item.setText(0, key)
            if isinstance(value, dict):
                self.build_tree(item, value)
            elif isinstance(value, int):
                item.setData(0, QtCore.Qt.UserRole, value)

    def selection_change(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        for index in selected.indexes():
            item = self.tree.itemFromIndex(index)
            column_index: int | None = item.data(0, QtCore.Qt.UserRole)
            if column_index is not None:
                self.selected_indicies.append(column_index)
        for index in deselected.indexes():
            item = self.tree.itemFromIndex(index)
            column_index: int | None = item.data(0, QtCore.Qt.UserRole)
            if column_index is not None:
                self.selected_indicies.remove(column_index)

        self.selected_names = [self.benchmark_data.benchmark_names[i] for i in self.selected_indicies]

        if len(self.selected_indicies) == 0:
            return

        column_names = get_columns(self.selected_indicies, self.benchmark_data)
        matrix = column_to_str_matrix(self.selected_indicies, self.benchmark_data, self.time_type)

        self.modify_table(column_names, self.benchmark_data.iteration_names, matrix)
        self.modify_toolbar(column_names, self.selected_names)

    def set_split_sizes(self):
        total = self.splitter.width()
        left = int(total * 0.3)
        right = total - left
        self.splitter.setSizes([left, right])

def show_gui(benchmark_data: BenchmarkData) -> int:
    app = QApplication(sys.argv)
    window = MainWindow(benchmark_data)
    window.show()
    return app.exec_()