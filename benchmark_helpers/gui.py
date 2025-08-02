from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore
import sys
from pathlib import Path

from benchmark_helpers.benchmark_data import BenchmarkColumn, BenchmarkData, BenchmarkEntry, TimeType

def get_columns(selected_column_indices: list[int], benchmark_data: BenchmarkData) -> list[str]:
    aggregated = False
    for index in selected_column_indices:
        aggregated = aggregated or benchmark_data.matrix[index].aggregated

    if not aggregated:
        columns = [['Time', 'Time Delta (%)']]
    else:
        columns = [['Mean Time', 'Mean Time Delta (%)'], 
                   ['Median Time', 'Median Time Delta (%)'], 
                   ['Standard Deviation', 'Standard Deviation Delta (%)'], 
                   ['Coefficient of Variation (%)', 'Coefficient of Variation Delta (%)']]

    flat_list = [
        value
        for col in columns
        for value in col
    ]
    return flat_list

def column_to_str_matrix(column: BenchmarkColumn, time_type: TimeType) -> list[list[str]]:
    matrix: list[list[str]] = []
    for entry in column:
        matrix.append(entry.get_row(column.aggregated, time_type))
    return matrix

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
        self.selected_names: list[int] = []

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
        table_data = column_to_str_matrix(self.benchmark_data.matrix[0], self.time_type)
        self.modify_table(column_names, row_names, table_data)
        return self.table

    def init_toolbar(self) -> QToolBar:
        self.toolbar = QToolBar('Main Toolbar')
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        column_names = get_columns(self.selected_indicies, self.benchmark_data)
        self.modify_toolbar(column_names, self.selected_indicies)
        return self.toolbar

    def init_tree(self) -> QTreeWidget:
        self.tree = QTreeWidget()
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

        # assert(input_column_count == len(table_data[0]))
        # assert(input_row_count == len(table_data))

        additional_column_names = [''] * max(min_column_count - input_column_count, 0)
        additional_row_names = [''] * max(min_row_count - input_row_count, 0)

        self.table.setColumnCount(column_count)
        self.table.setRowCount(row_count)
        
        self.table.setHorizontalHeaderLabels(columns_names + additional_column_names)
        self.table.setVerticalHeaderLabels(row_names + additional_row_names)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        for i in range(column_count):
            for j in range(row_count):
                if i < len(table_data[0]) and j < len(table_data):
                    text = table_data[j][i]
                    item = QTableWidgetItem(text)
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(j, i, item)
                else:
                    item = QTableWidgetItem('')
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(j, i, item)

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
            table_data = column_to_str_matrix(self.benchmark_data.matrix[0], self.time_type)
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
            main_benchmark_menu.addAction(selected_benchmark)

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
        matrix = column_to_str_matrix(self.benchmark_data.matrix[self.selected_indicies[0]], self.time_type)

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