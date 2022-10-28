#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import os
import sys

# Mechanism to support both PyQt and PySide
# -----------------------------------------

PYQT5 = "PyQt5"
PYQT6 = "PyQt6"
PYSIDE2 = "PySide2"
PYSIDE6 = "PySide6"
QT_LIB_ORDER = [PYQT5, PYSIDE2, PYSIDE6, PYQT6]
QT_LIB = os.getenv("PYQTGRAPH_QT_LIB")

# Parse optional cli argument to enfore a QT_LIB
# cli example: python benchmark.py pyside6
if len(sys.argv) > 1:
    arg1 = str(sys.argv[1]).upper()
    for i, lib in enumerate(QT_LIB_ORDER):
        if arg1 == lib.upper():
            QT_LIB = lib
            break

if QT_LIB is None:
    for lib in QT_LIB_ORDER:
        if lib in sys.modules:
            QT_LIB = lib
            break

if QT_LIB is None:
    for lib in QT_LIB_ORDER:
        try:
            __import__(lib)
            QT_LIB = lib
            break
        except ImportError:
            pass

if QT_LIB is None:
    this_file = __file__.split(os.sep)[-1]
    raise Exception(
        f"{this_file} requires PyQt5, PyQt6, PySide2 or PySide6; "
        "none of these packages could be imported."
    )

# fmt: off
# pylint: disable=import-error, no-name-in-module
if QT_LIB == PYQT5:
    from PyQt5 import QtWidgets as QtWid                   # type: ignore
elif QT_LIB == PYQT6:
    from PyQt6 import QtWidgets as QtWid                   # type: ignore
elif QT_LIB == PYSIDE2:
    from PySide2 import QtWidgets as QtWid                 # type: ignore
elif QT_LIB == PYSIDE6:
    from PySide6 import QtWidgets as QtWid                 # type: ignore
# pylint: enable=import-error, no-name-in-module
# fmt: on

# \end[Mechanism to support both PyQt and PySide]
# -----------------------------------------------

import numpy as np
import pyqtgraph as pg

TRY_USING_OPENGL = True
if TRY_USING_OPENGL:
    try:
        import OpenGL.GL as gl  # pylint: disable=unused-import
    except:  # pylint: disable=bare-except
        print("OpenGL acceleration: Disabled")
        print("To install: `conda install pyopengl` or `pip install pyopengl`")
    else:
        print("OpenGL acceleration: Enabled")
        pg.setConfigOptions(useOpenGL=True)
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(enableExperimental=True)

from dvg_pyqtgraph_threadsafe import BufferedPlotCurve

# ------------------------------------------------------------------------------
#   MainWindow
# ------------------------------------------------------------------------------


class MainWindow(QtWid.QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.setGeometry(350, 50, 800, 660)
        self.setWindowTitle("Demo: dvg_pyqtgraph_threadsafe")

        # GraphicsLayoutWidget
        self.gw = pg.GraphicsLayoutWidget()

        self.plot_1 = self.gw.addPlot()
        self.plot_1.showGrid(x=1, y=1)

        self.tscurve = BufferedPlotCurve(
            capacity=8,
            linked_curve=self.plot_1.plot(
                pen=pg.mkPen(color=[255, 255, 0], width=3)
            ),
        )

        self.tscurve.extendData([0, 1, 2, 3, 4], [0, 1, np.nan, 3, 3])
        self.tscurve.extendData([5, 6, 7, 8, 9], [4, 5, np.nan, 7, np.nan])
        self.tscurve.update()

        # Round up full window
        hbox = QtWid.QHBoxLayout(self)
        hbox.addWidget(self.gw, 1)


# ------------------------------------------------------------------------------
#   Main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    app = QtWid.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    if QT_LIB in (PYQT5, PYSIDE2):
        sys.exit(app.exec_())
    else:
        sys.exit(app.exec())
