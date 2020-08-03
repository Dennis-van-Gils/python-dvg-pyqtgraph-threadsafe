#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import numpy as np
from PyQt5 import QtWidgets as QtWid
import pyqtgraph as pg

from dvg_pyqtgraph_threadsafe import PlotCurve

USE_OPENGL = False
if USE_OPENGL:
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
            xRange=[0, 5], yRange=[0, 4], disableAutoRange=True,
        )

        capacity = 5
        self.tscurve = PlotCurve(
            capacity=capacity,
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
    sys.exit(app.exec_())
