#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets


class RangeFindingDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, locale: QtCore.QLocale, parent=None):
        super().__init__(parent)

        self.locale = locale

        delimiter = self.locale.decimalPoint()
        if delimiter == '.':
            delimiter = '\\' + delimiter

        regexp_parts = [
            r"\s*([+|-]?\d{1,3})|",
            r"([+|-]?\d{1,3}",
            delimiter,
            r"\d{1,4})|",
            r"([+|-]?\d{1,3}\s+[0-5]\d)|",
            r"([+|-]?\d{1,3}\s+[0-5]\d",
            delimiter,
            r"\d{1,2})"
        ]

        self.regexp = QtCore.QRegExp("".join(regexp_parts))

    def createEditor(self,
                     parent: QtWidgets.QWidget,
                     option: QtWidgets.QStyleOptionViewItem,
                     index:  QtCore.QModelIndex):

        column = index.column()
        if column == 0:
            widget = QtWidgets.QLineEdit(parent)
            validator = QtGui.QRegExpValidator(self.regexp, self)
            widget.setValidator(validator)

            return widget

        elif column == 1:
            widget = QtWidgets.QDoubleSpinBox(parent)
            widget.setLocale(self.locale)
            widget.setMinimum(0.0)
            widget.setMaximum(100.0)
            widget.setDecimals(3)
            widget.setSingleStep(0.001)

            return widget

        return super().createEditor(parent, option, index)

    def updateEditorGeometry(self,
                             editor: QtWidgets.QWidget,
                             option: QtWidgets.QStyleOptionViewItem,
                             index:  QtCore.QModelIndex):

        column = index.column()
        if column < 2 and editor is not None:
            editor.setGeometry(option.rect)

        super().updateEditorGeometry(editor, option, index)

    def setEditorData(self,
                      editor: QtWidgets.QWidget,
                      index: QtCore.QModelIndex):

        model = index.model()
        if model is not None:
            column = index.column()
            if column == 0 and \
                isinstance(editor, QtWidgets.QLineEdit):
                azimuth = float(model.data(index, QtCore.Qt.EditRole))
                angle = np.fabs(azimuth)

                deg = int(np.floor(angle))
                angle = int(np.round(6000.0 * (angle - deg)))
                iamin, famin = angle // 100, angle % 100
                sign = '-' if azimuth < 0.0 else '+'

                if azimuth == 0.0:
                    editor.setText(f"0 00{self.locale.decimalPoint()}00")
                else:
                    editor.setText(
                        "{}{} {:0>2}{}{:0>2}".format(
                            sign, deg, iamin, self.locale.decimalPoint(), famin
                        )
                    )

            elif column == 1 and \
                isinstance(editor, QtWidgets.QDoubleSpinBox):
                value = float(model.data(index, QtCore.Qt.EditRole))
                editor.setValue(value)
                return

        super().setEditorData(editor, index)

    def setModelData(self,
                     editor: QtWidgets.QWidget,
                     model:  QtCore.QAbstractItemModel,
                     index:  QtCore.QModelIndex):

        if model is not None:
            column = index.column()
            if column == 0 and \
                isinstance(editor, QtWidgets.QLineEdit):
                text_parts = editor.text().split(' ')
                angle_parts = []
                for text_part in text_parts:
                    if text_part:
                        angle_parts.append(self.locale.toFloat(text_part)[0])

                length = len(angle_parts)
                if length == 0:
                    value = 0.0
                else:
                    value = angle_parts[0]
                    sign = value < 0.0
                    value = np.fabs(value)

                    if length > 1:
                        value += angle_parts[1] / 60.0

                    if sign:
                        value = -value

                model.setData(index, value, QtCore.Qt.EditRole)
                return

            elif column == 1 and \
                isinstance(editor, QtWidgets.QDoubleSpinBox):
                model.setData(index, editor.value(), QtCore.Qt.EditRole)
                return

        super().setModelData(editor, model, index)
