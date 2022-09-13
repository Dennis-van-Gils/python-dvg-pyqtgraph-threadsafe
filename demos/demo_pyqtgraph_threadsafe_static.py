#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Mechanism to support both PyQt and PySide
# -----------------------------------------
import os
import sys

QT_LIB = os.getenv("PYQTGRAPH_QT_LIB")
PYSIDE = "PySide"
PYSIDE2 = "PySide2"
PYSIDE6 = "PySide6"
PYQT4 = "PyQt4"
PYQT5 = "PyQt5"
PYQT6 = "PyQt6"

# pylint: disable=import-error, no-name-in-module
# fmt: off
if QT_LIB is None:
    libOrder = [PYQT5, PYSIDE2, PYSIDE6, PYQT6]
    for lib in libOrder:
        if lib in sys.modules:
            QT_LIB = lib
            break

if QT_LIB is None:
    for lib in libOrder:
        try:
            __import__(lib)
            QT_LIB = lib
            break
        except ImportError:
            pass

if QT_LIB is None:
    raise Exception(
        "DvG_PyQtGraph_ThreadSafe requires PyQt5, PyQt6, PySide2 or PySide6; "
        "none of these packages could be imported."
    )

if QT_LIB == PYQT5:
    from PyQt5 import QtWidgets as QtWid                   # type: ignore
elif QT_LIB == PYQT6:
    from PyQt6 import QtWidgets as QtWid                   # type: ignore
elif QT_LIB == PYSIDE2:
    from PySide2 import QtWidgets as QtWid                 # type: ignore
elif QT_LIB == PYSIDE6:
    from PySide6 import QtWidgets as QtWid                 # type: ignore

# fmt: on
# pylint: enable=import-error, no-name-in-module
# \end[Mechanism to support both PyQt and PySide]
# -----------------------------------------------

import numpy as np
import pyqtgraph as pg

from dvg_pyqtgraph_threadsafe import PlotCurve

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
        self.plot_1.setRange(
            xRange=[0, 5],
            yRange=[0, 4],
            disableAutoRange=True,
        )

        self.tscurve = PlotCurve(
            linked_curve=self.plot_1.plot(
                pen=pg.mkPen(color=[255, 255, 0], width=3)
            ),
        )

        x = np.array([0, 1, 2, 3, 4])
        y = np.array([0, 1, np.nan, 3, 3])
        # x = np.array([np.nan] * 5)
        # y = np.array([np.nan] * 5)

        self.tscurve.setData(x, y)
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