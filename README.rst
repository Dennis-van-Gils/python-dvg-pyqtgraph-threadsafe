.. image:: https://img.shields.io/pypi/v/dvg-pyqtgraph-threadsafe
    :target: https://pypi.org/project/dvg-pyqtgraph-threadsafe
.. image:: https://img.shields.io/pypi/pyversions/dvg-pyqtgraph-threadsafe
    :target: https://pypi.org/project/dvg-pyqtgraph-threadsafe
.. image:: https://requires.io/github/Dennis-van-Gils/python-dvg-pyqtgraph-threadsafe/requirements.svg?branch=master
    :target: https://requires.io/github/Dennis-van-Gils/python-dvg-pyqtgraph-threadsafe/requirements/?branch=master
    :alt: Requirements Status
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/License-MIT-purple.svg
    :target: https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-threadsafe/blob/master/LICENSE.txt

DvG_PyQtGraph_ThreadSafe
========================
*PyQtGraph library providing thread-safe plot curves with underlying (ring)
buffers:* ``HistoryChartCurve``, ``BufferedPlotCurve`` & ``PlotCurve``.

- Github: https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-threadsafe
- PyPI: https://pypi.org/project/dvg-pyqtgraph-threadsafe

Installation::

    pip install dvg-pyqtgraph-threadsafe

Classes ``HistoryChartCurve``, ``BufferedPlotCurve`` & ``PlotCurve`` wrap around
a ``pyqtgraph.PlotDataItem`` class, called a *curve* for convenience. Data can
be safely appended or set from out of any thread. 

The (x, y)-curve data is buffered internally to the class, relying on either a
circular/ring buffer or a regular array buffer:

    HistoryChartCurve
        Ring buffer. The plotted x-data will be shifted such that the
        right-side is always set to 0. I.e., when `x` denotes time, the data is
        plotted backwards in time, hence the name *history* chart. The most
        recent data is on the right-side of the ring buffer.

    BufferedPlotCurve
        Ring buffer. Data will be plotted as is. Can also act as a Lissajous figure.

    PlotCurve
        Regular array buffer. Data will be plotted as is.

Usage:

    .. code-block:: python

        import sys
        from PyQt5 import QtWidgets
        import pyqtgraph as pg
        from dvg_pyqtgraph_threadsafe import HistoryChartCurve

        class MainWindow(QtWidgets.QWidget):
            def __init__(self, parent=None, **kwargs):
                super().__init__(parent, **kwargs)

                self.gw = pg.GraphicsWindow()
                self.plot_1 = self.gw.addPlot()
                
                # Create a HistoryChartCurve and have it wrap around a new PlotDataItem
                # as set by argument `linked_curve`.
                self.tscurve_1 = HistoryChartCurve(
                    capacity=5,
                    linked_curve=self.plot_1.plot(pen=pg.mkPen('r')),
                )

                grid = QtWidgets.QGridLayout(self)
                grid.addWidget(self.gw)

        app = QtWidgets.QApplication(sys.argv)
        window = MainWindow()

        # The following line could have been executed from inside of another thread:
        window.tscurve_1.extend_data([1, 2, 3, 4, 5], [10, 20, 30, 40, 50])
        
        # Redraw the curve from out of the main thread
        window.tscurve_1.update()

        window.show()
        sys.exit(app.exec_())

API
===

