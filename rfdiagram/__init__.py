#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

from PySide2 import QtCore
from PySide2 import QtWidgets

from .mainwindow import MainWindow
# noinspection PyUnresolvedReferences
from . import rfdiagram_rc


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationDomain("new-divos.ru")
    app.setApplicationName("rfdiagram")

    path = QtCore.QStandardPaths.writableLocation(
        QtCore.QStandardPaths.AppDataLocation
    )
    if not path:
        # noinspection PyArgumentList
        path = os.path.join(QtCore.QDir.tempPath(), "rfdiagram")

    app_dir = QtCore.QDir(path)
    path = app_dir.absolutePath()
    if app_dir.mkpath(path):
        log_path = os.path.join(path, "logs")
        app_dir.mkpath(log_path)
    else:
        print("Cannot create application data directory", file=sys.stderr)
        sys.exit(-1)

    logging.basicConfig(
        format="%(levelname)-8s [%(asctime)s] %(message)s",
        level=logging.DEBUG,
        filename=os.path.join(log_path, "rfdiagram.log")
    )

    translator = QtCore.QTranslator()
    locale = QtCore.QLocale()
    if translator.load(locale, "rfdiagram", "_", ":/languages"):
        app.installTranslator(translator)
        logging.info(f"The translator for the locale '{locale.name()}'"
                     " was loaded and installed")

    window = MainWindow(locale)
    logging.debug("The main window object has been created")
    window.showMaximized()
    logging.info("The main window has been shown")

    logging.info("Start the application event cycle")
    sys.exit(app.exec_())
