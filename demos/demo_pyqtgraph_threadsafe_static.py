#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import sys

from qtpy import QtWidgets as QtWid
import numpy as np
import pyqtgraph as pg

from dvg_pyqtgraph_threadsafe import BufferedPlotCurve

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
    app.exec()
