#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import numpy as np
import matplotlib.backends.backend_qt5agg as backend
from matplotlib.figure import Figure

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from .rfdelegate import RangeFindingDelegate
from .rfmodel import RangeFindingModel


# noinspection PyArgumentList, PyUnresolvedReferences
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, locale: QtCore.QLocale, parent=None):
        super().__init__(parent)
        self.locale = locale

        self.file_name = None
        self.is_dirty = False
        self.update_window_title()
        self.setWindowIcon(QtGui.QIcon(":/images/icon.png"))

        # Выполнить настройку виджетов программы
        self.docked = QtWidgets.QDockWidget(self.tr("Measurements"), self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,
                           self.docked)

        self.view = QtWidgets.QTableView(self)
        self.docked.setWidget(self.view)

        self.model = RangeFindingModel(locale, self)
        self.model.dataChanged.connect(self.on_data_changed)
        self.delegate = RangeFindingDelegate(locale, self)

        self.view.setItemDelegate(self.delegate)
        self.view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.view.setSortingEnabled(False)
        self.view.setModel(self.model)
        self.view.setAlternatingRowColors(True)

        self.view.selectionModel().selectionChanged.connect(
            lambda: self.update_status_bar()
        )

        table_header: QtWidgets.QHeaderView = self.view.horizontalHeader()
        table_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        table_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        # Выполнить создание и настройку действий программы
        self.new_action = QtWidgets.QAction(
            QtGui.QIcon(":/images/new.png"),
            self.tr("New"),
            self
        )
        self.new_action.setToolTip(self.tr(
            "Create a new range finding diagram file"
        ))
        self.new_action.setShortcut(QtGui.QKeySequence.New)
        self.new_action.triggered.connect(self.on_new)

        self.open_action = QtWidgets.QAction(
            QtGui.QIcon(":/images/open.png"),
            self.tr("Open..."),
            self
        )
        self.open_action.setToolTip(self.tr(
            "Open an existing range finding diagram file"
        ))
        self.open_action.setShortcut(QtGui.QKeySequence.Open)
        self.open_action.triggered.connect(self.on_open)

        self.save_action = QtWidgets.QAction(
            QtGui.QIcon(":/images/save.png"),
            self.tr("Save"),
            self
        )
        self.save_action.setToolTip(self.tr(
            "Save the current range finding diagram"
        ))
        self.save_action.setShortcut(QtGui.QKeySequence.Save)
        self.save_action.triggered.connect(self.on_save)
        self.save_action.setEnabled(False)

        self.save_as_action = QtWidgets.QAction(
            self.tr("Save As..."),
            self
        )
        self.save_as_action.setToolTip(self.tr(
            "Save the current range finding diagram as a file"
        ))
        self.save_as_action.setShortcut(QtGui.QKeySequence.SaveAs)
        self.save_as_action.triggered.connect(self.on_save_as)
        self.save_as_action.setEnabled(False)

        self.exit_action = QtWidgets.QAction(
            self.tr("Exit"),
            self
        )
        self.exit_action.setToolTip(self.tr("Exit the application"))
        self.exit_action.setShortcut(QtGui.QKeySequence.Quit)
        self.exit_action.triggered.connect(lambda: QtWidgets.qApp.closeAllWindows())

        self.add_action = QtWidgets.QAction(
            QtGui.QIcon(":/images/add.png"),
            self.tr("Add"),
            self
        )
        self.add_action.setToolTip(self.tr(
            "Insert row into the table after the selected row"
        ))
        self.add_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL |
                                                       QtCore.Qt.Key_I))
        self.add_action.triggered.connect(self.on_add_row)

        self.remove_action = QtWidgets.QAction(
            QtGui.QIcon(":/images/remove.png"),
            self.tr("Remove"),
            self
        )
        self.remove_action.setToolTip(self.tr(
            "Remove the selected row from the table"
        ))
        self.remove_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL |
                                                          QtCore.Qt.Key_R))
        self.remove_action.triggered.connect(self.on_remove_row)
        self.remove_action.setEnabled(False)

        self.clear_action = QtWidgets.QAction(
            QtGui.QIcon(":/images/clear.png"),
            self.tr("Clear"),
            self
        )
        self.clear_action.setToolTip(self.tr("Clear the table"))
        self.clear_action.triggered.connect(self.on_clear)
        self.clear_action.setEnabled(False)

        self.plot_action = QtWidgets.QAction(
            QtGui.QIcon(":/images/polarplot.png"),
            self.tr("Plot"),
            self
        )
        self.plot_action.setToolTip(self.tr("Plot the range finding diagram"))
        self.plot_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL |
                                                        QtCore.Qt.Key_D))
        self.plot_action.triggered.connect(self.on_plot)
        self.plot_action.setEnabled(False)

        self.save_plot_as_action = QtWidgets.QAction(
            QtGui.QIcon(":images/saveimage.png"),
            self.tr("Save Plot As..."),
            self
        )
        self.save_plot_as_action.setToolTip(self.tr(
            "Save the current range finding diagram plot as an image file"
        ))
        self.save_plot_as_action.setShortcut(QtGui.QKeySequence("Ctrl+Alt+S"))
        self.save_plot_as_action.triggered.connect(self.on_save_plot)
        self.save_plot_as_action.setEnabled(False)

        docked_visibility_action: QtWidgets.QAction = \
            self.docked.toggleViewAction()
        docked_visibility_action.setText(self.tr("Measurements Panel"))
        docked_visibility_action.setToolTip(self.tr(
            "Show/hide the Measurements Panel"
        ))
        docked_visibility_action.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL |
                                                                QtCore.Qt.Key_1))

        # Выполнить настройку меню программы
        file_menu: QtWidgets.QMenu = self.menuBar().addMenu(self.tr("File"))
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_plot_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu: QtWidgets.QMenu = self.menuBar().addMenu(self.tr("Edit"))
        edit_menu.addAction(self.add_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.remove_action)
        edit_menu.addAction(self.clear_action)

        view_menu: QtWidgets.QMenu = self.menuBar().addMenu(self.tr("View"))
        view_menu.addAction(docked_visibility_action)

        plot_menu: QtWidgets.QMenu = self.menuBar().addMenu(self.tr("Plot"))
        plot_menu.addAction(self.plot_action)

        # Выполнить настройку панелей инструментов программы
        file_toolbar: QtWidgets.QToolBar = self.addToolBar("File")
        file_toolbar.addAction(self.new_action)
        file_toolbar.addAction(self.open_action)
        file_toolbar.addAction(self.save_action)
        file_toolbar.addSeparator()
        file_toolbar.addAction(self.save_plot_as_action)

        edit_toolbar: QtWidgets.QToolBar = self.addToolBar("Edit")
        edit_toolbar.addAction(self.add_action)
        edit_toolbar.addSeparator()
        edit_toolbar.addAction(self.remove_action)
        edit_toolbar.addAction(self.clear_action)

        plot_toolbar: QtWidgets.QMenu = self.addToolBar("Plot")
        plot_toolbar.addAction(self.plot_action)

        # Выполнить настройку панели статуса
        self.status_bar_message_timeout = 2000

        self.location_label = QtWidgets.QLabel(" 999:999 ", self)
        self.location_label.setAlignment(QtCore.Qt.AlignCenter)
        self.location_label.setMinimumSize(self.location_label.sizeHint())

        self.measurement_label = QtWidgets.QLabel(self)
        self.measurement_label.setIndent(10)

        self.statusBar().addWidget(self.location_label)
        self.statusBar().addWidget(self.measurement_label)

        self.update_status_bar()

        # Добавить виджеты для отображения графика
        self.figure = Figure()
        self.canvas = backend.FigureCanvasQTAgg(self.figure)
        self.setCentralWidget(self.canvas)
        self.is_plotted = False

        axes = self.figure.get_axes()
        if len(axes) == 0:
            ax = self.figure.add_subplot(111, projection='polar')

            ax.set_rmax(50.0)
            ax.grid(True)

            self.canvas.draw()

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.ok_to_continue():
            logging.info("Start to close the main window."
                         " The application will finish work")
            event.accept()
        else:
            event.ignore()

    def update_window_title(self):
        result = [ "[" ]
        if self.file_name is None:
            result.append(self.tr("Untitled"))
            result.append(".json")
        else:
            result.append(QtCore.QFileInfo(self.file_name).fileName())

        if self.is_dirty:
            result.append("*")
        result.append("] - ")
        result.append(self.tr("Range Finding Diagram"))

        self.setWindowTitle(''.join(result))

    def update_actions(self):
        model_is_not_empty = not self.model.empty()

        self.remove_action.setEnabled(model_is_not_empty)
        self.clear_action.setEnabled(model_is_not_empty)
        self.plot_action.setEnabled(model_is_not_empty)

        self.save_plot_as_action.setEnabled(self.is_plotted)

        can_save = model_is_not_empty and self.is_dirty

        self.save_action.setEnabled(can_save)
        self.save_as_action.setEnabled(can_save)

    def update_status_bar(self):
        if self.model.empty():
            self.location_label.setText(" 0:0 ")
            self.measurement_label.setText(self.tr(
                "The measurements are not provided"
            ))

        else:
            selection_model: QtCore.QItemSelectionModel = \
                self.view.selectionModel()

            azimuth_str, distance_str, row = None, None, 0
            for index in selection_model.selectedIndexes():
                if index.column() == 0:
                    azimuth_str = self.model.data(index, QtCore.Qt.DisplayRole)
                    row = index.row()
                elif index.column() == 1:
                    distance_str = self.model.data(index, QtCore.Qt.DisplayRole)

            if not azimuth_str or not distance_str:
                self.measurement_label.setText(self.tr(
                    "The measurement is not selected"
                ))
            else:
                self.measurement_label.setText(
                    "{} = {}; {} = {}".format(
                        self.tr("Azimuth"),
                        azimuth_str,
                        self.tr("Distance"),
                        distance_str
                    )
                )

            self.location_label.setText(f" {row + 1}:{self.model.rowCount()} ")

    def clear_plot(self):
        axes = self.figure.get_axes()
        if len(axes) == 0:
            ax = self.figure.add_subplot(111, projection='polar')
        else:
            ax = axes[0]
        ax.clear()

        ax.set_rmax(50.0)
        ax.grid(True)

        self.canvas.draw()
        self.is_plotted = False

    def load_file(self, file_name: str):
        if file_name:
            try:
                with open(file_name, mode='r', encoding='utf-8') as fin:
                    json_lines = fin.readlines()

                if self.model.from_json('\n'.join(json_lines)):
                    self.is_dirty = False
                    self.file_name = file_name

                    self.update_actions()
                    self.update_window_title()

                    logging.debug(f"The file {file_name} was successfully loaded")
                    self.statusBar().showMessage(self.tr("File loaded"),
                                                 self.status_bar_message_timeout)
                    return True
                else:
                    logging.error(f"Cannot read data from the JSON file: {file_name}")

            except OSError as exc:
                logging.error(
                    "An exception occurred during loading "
                    f"from the file {file_name}: {exc.strerror}"
                )

        self.statusBar().showMessage(self.tr("Loading cancelled"),
                                     self.status_bar_message_timeout)
        return False

    def save_file(self, file_name: str):
        if not self.model.empty():
            if file_name:
                try:
                    with open(file_name, mode='w', encoding='utf-8') as fout:
                        fout.write(self.model.to_json())

                    self.file_name = file_name
                    self.is_dirty = False
                    self.update_window_title()
                    self.update_actions()

                    logging.debug(f"The file {file_name} was successfully saved")
                    self.statusBar().showMessage(self.tr("File saved"),
                                                 self.status_bar_message_timeout)
                    return True

                except OSError as exc:
                    logging.error(
                        "An exception occurred during saving "
                        f"to the file {file_name}: {exc.strerror}"
                    )
            else:
                logging.error(
                    "Cannot use an empty file name for saving"
                )
        else:
            logging.error(
                f"Cannot save an empty model to the file {file_name}"
            )

        self.statusBar().showMessage(self.tr("Saving cancelled"),
                                     self.status_bar_message_timeout)
        return False

    def ok_to_continue(self):
        if self.is_dirty:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setWindowTitle(self.tr("Range Finding Diagram"))
            msg_box.setText(self.tr("The document has been modified."))
            msg_box.setInformativeText(self.tr("Do you want to save your changes?"))
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Save |
                                       QtWidgets.QMessageBox.Discard |
                                       QtWidgets.QMessageBox.Cancel)
            msg_box.setDefaultButton(QtWidgets.QMessageBox.Save)
            msg_box.setEscapeButton(QtWidgets.QMessageBox.Cancel)

            msg_box.button(QtWidgets.QMessageBox.Save).setText(self.tr("Save"))
            msg_box.button(QtWidgets.QMessageBox.Discard).setText(self.tr("Don't save"))
            msg_box.button(QtWidgets.QMessageBox.Cancel).setText(self.tr("Cancel"))

            result = msg_box.exec_()

            if result == QtWidgets.QMessageBox.Yes:
                return save()
            elif result == QtWidgets.QMessageBox.Cancel:
                return False

        return True

    @QtCore.Slot()
    def on_new(self):
        if self.ok_to_continue():
            self.model.clear()
            self.clear_plot()

            self.file_name = None
            self.is_dirty = False

            self.update_actions()
            self.update_window_title()
            self.update_status_bar()

    @QtCore.Slot()
    def on_open(self):
        if self.ok_to_continue():
            documents_path = QtCore.QStandardPaths.writableLocation(
                QtCore.QStandardPaths.DocumentsLocation
            )
            if not documents_path:
                documents_path = QtCore.QDir.homePath()

            file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
                parent=self,
                caption=self.tr("Open Range Finding Diagram"),
                dir=documents_path,
                filter=self.tr("JSON files (*.json)")
            )

            if file_name:
                if self.load_file(file_name):
                    if not self.model.empty():
                        self.view.setCurrentIndex(self.model.index(0, 0))

                    self.on_plot()

                else:
                    err_msg_box = QtWidgets.QMessageBox(self)
                    err_msg_box.setIcon(QtWidgets.QMessageBox.Critical)
                    err_msg_box.setWindowTitle(self.tr("Error"))
                    err_msg_box.setText(
                        self.tr("Could not load JSON file {}").format(file_name)
                    )
                    err_msg_box.setDetailedText(self.tr(
                        "See detailed information in .log file of the application"
                    ))
                    err_msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)

                    err_msg_box.exec_()

    @QtCore.Slot()
    def on_save(self):
        if not self.file_name:
            return self.on_save_as()
        else:
            return self.save_file(self.file_name)

    @QtCore.Slot()
    def on_save_as(self):
        documents_path = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.DocumentsLocation
        )
        if not documents_path:
            documents_path = QtCore.QDir.homePath()

        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption=self.tr("Save Range Finding Diagram"),
            dir=documents_path,
            filter=self.tr("JSON files (*.json)")
        )

        return self.save_file(file_name) if file_name else False

    @QtCore.Slot()
    def on_add_row(self):
        selection: QtCore.QItemSelection = \
            self.view.selectionModel().selection()

        if selection.empty():
            self.model.insertRow(self.model.rowCount())
        else:
            rows = set()
            for index in selection.indexes():
                rows.add(index.row())

            for row in rows:
                self.model.insertRow(row + 1)

        self.clear_plot()
        self.update_actions()

        self.is_dirty = True
        self.update_window_title()
        self.update_status_bar()

    @QtCore.Slot()
    def on_remove_row(self):
        selection: QtCore.QItemSelection = \
            self.view.selectionModel().selection()
        if selection.empty():
            return

        rows = set()
        for index in selection.indexes():
            rows.add(index.row())

        for row in rows:
            self.model.removeRow(row)

        self.clear_plot()
        self.update_actions()

        self.is_dirty = True
        self.update_window_title()
        self.update_status_bar()

    @QtCore.Slot()
    def on_clear(self):
        self.model.clear()

        self.clear_plot()
        self.update_actions()

        self.is_dirty = True
        self.update_window_title()
        self.update_status_bar()

    @QtCore.Slot()
    def on_plot(self):
        axes = self.figure.get_axes()
        if len(axes) == 0:
            ax = self.figure.add_subplot(111, projection='polar')
        else:
            ax = axes[0]
        ax.clear()

        is_valid, theta, r, f = self.model.prepare()

        if is_valid:
            ax.grid(True)

            new_theta = np.linspace(
                np.min(theta),
                np.max(theta),
                1000,
                endpoint=True
            )
            new_r = f(new_theta)
            ax.plot(new_theta, new_r, color='maroon', linestyle='--')
            ax.plot(theta, r, color='darkblue', marker='o', linestyle='none')

            max_r = np.max(r)
            max_new_r = np.max(new_r)
            if max_r < max_new_r:
                max_r = max_new_r
            ax.set_rmax(max_r + 10.0 if max_r > 50.0 else 50.0)

        self.canvas.draw()
        self.is_plotted = True
        self.update_actions()

    @QtCore.Slot()
    def on_save_plot(self):
        assert self.is_plotted

        pictures_path = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.PicturesLocation
        )
        if not pictures_path:
            pictures_path = QtCore.QDir.homePath()

        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption=self.tr("Save Plot"),
            dir=pictures_path
        )

        if file_name:
            self.figure.savefig(file_name)

    @QtCore.Slot()
    def on_data_changed(self):
        self.clear_plot()

        self.is_dirty = True
        self.update_window_title()
        self.update_status_bar()
