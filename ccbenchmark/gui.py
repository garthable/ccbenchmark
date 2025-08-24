from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore, QtGui
import sys

from ccbenchmark.benchmark_data import BenchmarkColumn, BenchmarkData, BenchmarkEntry, TimeType, compute_delta_percentage
from ccbenchmark.util import time_to_str

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

def get_csv(matrix: list[list[str | float]], deliminator=b',') -> bytes:
    data = b''
    for row in matrix:
        data_row = ''
        for entry in row:
            text = f'"{entry}"' if type(entry) is str else f'{entry}'
            data_row += f'{text}' if data_row == '' else f'{deliminator}{text}'
            
        data += f'{data_row}'.encode() if data == b'' else f'\n{data_row}'.encode()
    return data

class Table(QTableWidget):
    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.copy()
        else:
            super().keyPressEvent(event)
    def copy(self) -> None:
        data = get_csv(self.get_selected_matrix(), deliminator='\t').decode()
        QApplication.clipboard().setText(data)

    def get_selected_matrix(self) -> list[list[str | float]]:
        selected_ranges = self.selectedRanges()
        if not selected_ranges or len(selected_ranges) == 0:
            return
        selected_range = selected_ranges[0]
        matrix = []
        row_text = ["Label"]
        for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
            if self.isColumnHidden(col):
                continue
            item = self.horizontalHeaderItem(col)
            row_text.append(item.text())
        matrix.append(row_text)

        for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
            item = self.verticalHeaderItem(row)
            row_text = [item.text()]
            for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                if self.isColumnHidden(col):
                    continue
                item = self.item(row, col)
                row_text.append(item.text())
            matrix.append(row_text)
        return matrix

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

    def init_table(self) -> Table:
        self.table = Table()
        self.modify_table()
        return self.table

    def init_toolbar(self) -> QToolBar:
        self.toolbar = QToolBar('Main Toolbar')
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        column_names = self.benchmark_data.get_columns(self.selected_indicies)
        self.modify_toolbar(column_names, self.selected_names)
        return self.toolbar

    def init_tree(self) -> QTreeWidget:
        self.tree = QTreeWidget()
        self.tree.model().setHeaderData(0, QtCore.Qt.Horizontal, 'Benchmarks')
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        data = self.benchmark_data.data_to_dict()
        self.build_tree(self.tree, data)
        return self.tree
    
    def init_selmodel(self) -> QtCore.QItemSelectionModel:
        return self.tree.selectionModel()

    def modify_table(self):
        columns_names = self.benchmark_data.get_columns(self.selected_indicies)
        row_names = self.benchmark_data.get_rows(self.selected_indicies)
        table_data = self.benchmark_data.column_to_str_matrix(self.selected_indicies, self.time_type)

        min_column_count = 30
        min_row_count = 50

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
                    
                    red_color = QtGui.QColor(255, 85, 85)
                    green_color = QtGui.QColor(0, 255, 128)
                    default_color = self.table.palette().color(QtGui.QPalette.Text)

                    def get_color() -> QtGui.QColor:
                        col_name = columns_names[i]
                        text_split = text.split(' ')
                        if len(text_split) == 0:
                            return default_color
                        try:
                            val = float(text_split[0])
                        except:
                            return default_color

                        if 'Δ' in col_name:
                            t = val / 20.0
                            t = max(min(t, 1.0), -1.0)
                            if t < 0.0:
                                t = abs(t)
                                selected_color = green_color
                            else:
                                selected_color = red_color
                            return QtGui.QColor(
                                int((1.0 - t)*default_color.red() + t*selected_color.red()),
                                int((1.0 - t)*default_color.green() + t*selected_color.green()),
                                int((1.0 - t)*default_color.blue() + t*selected_color.blue())
                            )
                        elif 'CV' in col_name:
                            if val > 10.0:
                                return red_color

                        return default_color


                    item.setForeground(QtGui.QBrush(get_color()))
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    
                    self.table.setItem(j, i, item)
                else:
                    item = QTableWidgetItem('')
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(j, i, item)

        default_width = self.table.horizontalHeader().defaultSectionSize()
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setMinimumSectionSize(default_width)

        self.preserve_max_vertical_header_width()
        self.hide_empty_columns()
        self.hide_empty_rows()

    def preserve_max_vertical_header_width(self):
        vertical_header = self.table.verticalHeader()
        font_metrics = QtGui.QFontMetrics(vertical_header.font())

        max_label_width = 0
        for row_index in range(self.table.rowCount()):
            item = self.table.verticalHeaderItem(row_index)
            if item is None:
                continue
            width = font_metrics.width(item.text())
            max_label_width = max(max_label_width, width)
        
        self.table.verticalHeader().setMinimumWidth(max_label_width)

    def hide_empty_columns(self) -> int:
        for col_index in range(self.table.columnCount()):
            toggle_row = False
            for row_index in range(self.table.rowCount()):
                item = self.table.item(row_index, col_index)
                if item is None:
                    continue
                text = item.text().strip()
                if text == 'N/A':
                    toggle_row = True
                elif text != '':
                    toggle_row = False
                    break
            if toggle_row:
                self.table.hideColumn(col_index)
            else:
                self.table.showColumn(col_index)
    
    def hide_empty_rows(self):
        for row_index in range(self.table.rowCount()):
            toggle_row = False
            for col_index in range(self.table.columnCount()):
                item = self.table.item(row_index, col_index)
                if item is None:
                    continue
                text = item.text().strip()
                if text == 'N/A':
                    toggle_row = True
                elif text != '':
                    toggle_row = False
                    break
            if toggle_row:
                self.table.hideRow(row_index)
            else:
                self.table.showRow(row_index)

    def to_matrix(self) -> list[list[str | float]]:
        data = []
        data_row = ['Label']
        for col in range(self.table.columnCount()):
            text = self.table.horizontalHeaderItem(col).text()
            if text == '':
                continue
            data_row.append(text)
        data.append(data_row)
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            header = self.table.verticalHeaderItem(row).text()
            if header == '':
                continue
            data_row = [header]
            for col in range(self.table.columnCount()):
                if self.table.isColumnHidden(col):
                    continue
                item = self.table.item(row, col)
                if item is None or item.text().strip() == '':
                    continue
                data_row.append(item.text())

            data.append(data_row)
        return data

    def export_to_csv(self):
        file = QFileDialog(self)
        data = get_csv(self.to_matrix())
        file.saveFileContent(data, f'benchmark.csv')

    def modify_toolbar(self, columns: list[str], selected_benchmarks: list[str]):
        self.toolbar.clear()
        show_stats_menu = DropdownChecks('Shown Stats', self.toolbar, self)

        def toggle_cpu_real_time():
            action: QAction = self.sender()
            if action.text() == 'Real Time':
                self.time_type = TimeType.REAL
            elif action.text() == 'CPU Time':
                self.time_type = TimeType.CPU
            
            self.modify_table()
        
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

        actions = ['Real Time', 'CPU Time'] if self.time_type == TimeType.REAL else ['CPU Time', 'Real Time']

        time_type_dropdown = DropdownSelect(self.toolbar, self)
        for action in actions:
            time_type_dropdown.addAction(action, toggle_cpu_real_time)
        
        main_benchmark_menu = DropdownSelect(self.toolbar, self)
        for selected_benchmark in selected_benchmarks:
            main_benchmark_menu.addAction(selected_benchmark, self.change_parent_selected)

        export_to_csv_button = QToolButton()
        export_to_csv_button.setText('CSV')
        export_to_csv_button.clicked.connect(self.export_to_csv)
        self.toolbar.addWidget(export_to_csv_button)

    def change_parent_selected(self):
        action: QAction = self.sender()
        name = action.text()
        try:
            index = self.selected_names.index(name)
        except ValueError:
            return
        self.selected_names.insert(0, self.selected_names.pop(index))
        self.selected_indicies.insert(0, self.selected_indicies.pop(index))

        self.modify_table()

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

        column_names = self.benchmark_data.get_columns(self.selected_indicies)

        self.modify_table()
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