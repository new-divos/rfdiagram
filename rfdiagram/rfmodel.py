#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import numpy as np
from scipy import interpolate

from PySide2 import QtCore


# noinspection PyArgumentList, PyUnresolvedReferences
class RangeFindingModel(QtCore.QAbstractTableModel):

    def __init__(self, locale: QtCore.QLocale, parent=None):
        super().__init__(parent)

        self.locale = locale
        self.measurements = None

    def data(self, index: QtCore.QModelIndex, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or self.measurements is None:
            return None

        row, column = index.row(), index.column()
        azimuth, distance = self.measurements[index.row(), :2]

        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                angle = np.fabs(azimuth)

                deg = int(np.floor(angle))
                angle = int(np.round(6000.0 * (angle - deg)))
                iamin, famin = angle // 100, angle % 100

                if azimuth < 0.0:
                    sign = '-'
                elif azimuth > 0.0:
                    sign = '+'
                else:
                    sign = ' '

                return "{}{}\u00B0 {:0>2}{}{:0>2}\u2032".format(
                    sign, deg, iamin, self.locale.decimalPoint(), famin
                )

            elif column == 1:
                distance = int(np.round(1000.0 * distance))
                idistance, fdistance = distance // 1000, distance % 1000

                return "{}{}{:0>3}".format(
                    idistance, self.locale.decimalPoint(), fdistance
                )

        elif role == QtCore.Qt.EditRole:
            if column == 0:
                return azimuth
            elif column == 1:
                return distance

        elif role == QtCore.Qt.TextAlignmentRole and column < 2:
            return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        return None

    def setData(self, index: QtCore.QModelIndex, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or self.measurements is None:
            return

        if role == QtCore.Qt.EditRole:
            row, column = index.row(), index.column()

            modified = False
            if column == 0:
                self.measurements[row, 0] = np.float32(value)
                modified = True
            elif column == 1:
                self.measurements[row, 1] = np.float32(value)
                modified = True

            if modified:
                self.dataChanged.emit(index, index, [ QtCore.Qt.EditRole ])

    def headerData(self, section: int, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return self.tr("Azimuth")
                elif section == 1:
                    return self.tr("Distance")
            elif orientation == QtCore.Qt.Vertical:
                return self.locale.toString(section + 1)

        return None

    def columnCount(self, index=QtCore.QModelIndex()):
        return 2

    def rowCount(self, index=QtCore.QModelIndex()):
        return self.measurements.shape[0] if self.measurements is not None else 0

    def insertRows(self, row: int, count: int, parent=QtCore.QModelIndex()):
        if row < 0 or count <= 0:
            return False

        if self.measurements is None:
            if row == 0:
                # Если данных измерений нет, то создать заполненный нулями массив
                self.beginInsertRows(parent, row, row + count - 1)
                self.measurements = np.zeros((count, 2), dtype=np.float32)
                self.endInsertRows()

                return True

        else:
            if row < self.measurements.shape[0]:
                # Выполнить объединение по вертикали текущего массива измерений
                # с массивом, заполненным нулями, предварительно разделив
                # текущий массив измерений на две части, в случае, если требуется
                # выполнить вставку строк в середину модели.
                self.beginInsertRows(parent, row, row + count - 1)
                self.measurements = np.vstack((
                    self.measurements[:row, :].copy(),
                    np.zeros((count, 2), dtype=np.float32),
                    self.measurements[row:, :].copy()
                ))
                self.endInsertRows()

                return True

            elif row == self.measurements.shape[0]:
                # Если требуется добавить строки в конец модели, то выполнить
                # объединение по вертикали текущего массива измерений с
                # массивом, заполненным нулями.
                self.beginInsertRows(parent, row, row + count - 1)
                self.measurements = np.vstack((
                    self.measurements,
                    np.zeros((count, 2), dtype=np.float32)
                ))
                self.endInsertRows()

                return True

        return False

    def removeRows(self, row: int, count: int, parent=QtCore.QModelIndex()):
        if row < 0 or count <= 0 or self.measurements is None:
            return False

        end = min(row + count, self.measurements.shape[0])

        if row == 0:

            self.beginRemoveRows(parent, row, end - 1)
            if end == self.measurements.shape[0]:
                # Требуется удалить весь набор измерений
                self.measurements = None
            else:
                # Требуется удалить часть данных с начала массива
                self.measurements = self.measurements[end:, :].copy()

            self.endRemoveRows()

            return True

        elif row < self.measurements.shape[0]:

            self.beginRemoveRows(parent, row, end - 1)
            if end == self.measurements.shape[0]:
                # Требуется удалить часть данных с конца массива
                self.measurements = self.measurements[:row, :].copy()
            else:
                # Требуется удалить часть данных из середины массива
                self.measurements = np.vstack((
                    self.measurements[:row, :].copy(),
                    self.measurements[end:, :].copy()
                ))

            self.endRemoveRows()

            return True

        return False

    def clear(self):
        if self.measurements is not None:
            self.beginRemoveRows(QtCore.QModelIndex(),
                                 0,
                                 self.measurements.shape[0] - 1)
            self.measurements = None
            self.endRemoveRows()

    def empty(self):
        return self.measurements is None

    def flags(self, index: QtCore.QModelIndex):
        if not index.isValid() or self.measurements is None:
            return 0

        if index.row() < self.measurements.shape[0] and index.column() < 2:
            return QtCore.Qt.ItemIsSelectable | \
                   QtCore.Qt.ItemIsEnabled | \
                   QtCore.Qt.ItemIsEditable

        return QtCore.Qt.ItemIsEnabled

    def prepare(self):
        if self.measurements is None:
            return False, None, None, None

        items = []
        for i in range(self.measurements.shape[0]):
            azimuth = self.measurements[i, 0]
            azimuth -= 360.0 * np.floor(azimuth / 360.0)
            items.append((azimuth * np.pi / 180.0,
                          self.measurements[i, 1]))

        items = list(sorted(items, key=lambda item: item[0]))
        items.append((items[0][0] + 2.0 * np.pi, items[0][1]))

        length = len(items)
        azimuths = np.zeros((length,), dtype=np.float32)
        distances = np.zeros((length,), dtype=np.float32)

        for i, (azimuth, distance) in enumerate(items):
            azimuths[i] = azimuth
            distances[i] = distance

        return True, azimuths, distances, \
               interpolate.interp1d(
                   azimuths,
                   distances,
                   kind='cubic',
                   fill_value='extrapolate'
               )

    def to_json(self):
        values = []
        if self.measurements is not None:
            for i in range(self.measurements.shape[0]):
                values.append(dict(azimuth=float(self.measurements[i, 0]),
                                   distance=float(self.measurements[i, 1])))

        return json.dumps(dict(measurements=values, version="1.0"))

    def from_json(self, json_data: str):
        try:
            self.beginResetModel()
            content = json.loads(json_data)

            # Получить версию файла с данными
            version = content.get('version', None)
            if not version:
                logging.error("Cannot retrieve version of JSON data")
                return False

            elif version == "1.0":
                measurements = content.get('measurements', None)
                if not measurements:
                    logging.error("Cannot retrieve measurements from JSON data")
                    return False

                self.measurements = np.zeros((len(measurements), 2))
                for i, measurement in enumerate(measurements):
                    for key, value in measurement.items():
                        if key == 'azimuth':
                            self.measurements[i, 0] = np.float32(value)
                        elif key == 'distance':
                            self.measurements[i, 1] = np.float32(value)
                        else:
                            logging.warning(f"Unrecognized key {key} in JSON data")

                return True, None

        except json.JSONDecodeError as exc:
            logging.error(f"An exception occurred during reading JSON data: {exc.msg}")
            return False

        finally:
            self.endResetModel()
