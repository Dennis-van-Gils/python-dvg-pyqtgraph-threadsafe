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
buffers.*

- Github: https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-threadsafe
- PyPI: https://pypi.org/project/dvg-pyqtgraph-threadsafe

Installation::

    pip install dvg-pyqtgraph-threadsafe

Classes ``HistoryChartCurve``, ``BufferedPlotCurve`` & ``PlotCurve`` wrap around
a ``pyqtgraph.PlotDataItem`` instance, called a *curve* for convenience. Data
can be safely appended or set from out of any thread.

The (x, y)-curve data is buffered internally to the class, relying on either a
circular/ring buffer or a regular array buffer:

    HistoryChartCurve
        Ring buffer. The plotted x-data will be shifted such that the
        right-side is always set to 0. I.e., when `x` denotes time, the data is
        plotted backwards in time, hence the name *history* chart. The most
        recent data is on the right-side of the ring buffer.

    BufferedPlotCurve
        Ring buffer. Data will be plotted as is. Can also act as a Lissajous
        figure.

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


``class ThreadSafeCurve(capacity: int, linked_curve: pg.PlotDataItem, shift_right_x_to_zero: bool = False, use_ringbuffer: bool = True)``
-----------------------------------------------------------------------------------------------------------------------------------------

    Provides the base class for a thread-safe plot *curve* to which
    (x, y)-data can be safely appended or set from out of any thread. It
    will wrap around the passed argument ``linked_curve`` of type
    ``pyqtgraph.PlotDataItem`` and will manage the (x, y)-data buffers
    underlying the curve.

    Intended multithreaded operation: One thread pushes new data into the
    ``ThreadSafeCurve``-buffers. Another thread performs the GUI refresh by
    calling ``update()`` which will redraw the curve according to the
    current buffer contents.

        Args:
            capacity (``int``):
                Maximum number of (x, y)-data points the buffer can store.

            linked_curve (``pyqtgraph.PlotDataItem``):
                Instance of ``pyqtgraph.PlotDataItem`` to plot the buffered
                data out into.

            shift_right_x_to_zero (``bool``, optional):
                When plotting, should the x-data be shifted such that the
                right-side is always set to 0? Useful for history charts.

                Default: False

            use_ringbuffer (``bool``, optional):
                When True, the (x, y)-data buffers are each a ring buffer. New
                readings are placed at the end (right-side) of the buffer,
                pushing out the oldest readings when the buffer has reached its
                maximum capacity (FIFO). Use methods ``append_data()`` and
                ``extend_data()`` to push in new data.

                When False, the (x, y)-data buffers are each a regular array
                buffer. Use method ``set_data()`` to set the data.

                Default: True

        Attributes:
            x_axis_divisor (``float``):
                The x-data in the buffer will be divided by this factor when the
                plot curve is drawn. Useful to, e.g., transform the x-axis units
                from milliseconds to seconds or minutes.

                Default: 1

            y_axis_divisor (``float``):
                Same functionality as ``x_axis_divisor``.

                Default: 1

Methods
-------
* ``apply_downsampling(state: bool = True, ds=4)``
    Downsample the curve by using PyQtGraph's build-in method
    ``pyqtgraph.PlotDataItem.setDownsampling()``.

* ``append_data(x, y):``
    Append a single (x, y)-data point to the ring buffer.

* ``extend_data(x_list, y_list):``
    Extend the ring buffer with a list of (x, y)-data points.

* ``set_data(x_list, y_list):``
    Set the (x, y)-data of the regular array buffer.

* ``update():``
    Update the data behind the curve, based on the current contents of
    the buffer, and redraw the curve on screen.

* ``clear():``
    Clear the contents of the curve and redraw.

* ``is_visible() -> bool``
* ``set_visible(state: bool = True)``

Properties
----------
* ``size -> Tuple[int, int]``:
    Number of elements currently contained in the underlying (x, y)-
    buffers of the curve. Note that this is not necessarily the number of
    elements of the currently drawn curve, but reflects the data buffer
    behind it that will be drawn onto screen by the next call to
    ``update()``.

``class HistoryChartCurve(capacity: int, linked_curve: pg.PlotDataItem)``
--------------------------------------------------------------------------
    Bases: ``ThreadSafeCurve``

    Provides a thread-safe curve with underlying ring buffers for the
    (x, y)-data. New readings are placed at the end (right-side) of the
    buffer, pushing out the oldest readings when the buffer has reached its
    maximum capacity (FIFO). Use methods ``append_data()`` and
    ``extend_data()`` to push in new data.

    The plotted x-data will be shifted such that the right-side is always
    set to 0. I.e., when ``x`` denotes time, the data is plotted backwards
    in time, hence the name *history* chart.

    See class ``ThreadSafeCurve`` for more details.

``class BufferedPlotCurve(capacity: int, linked_curve: pg.PlotDataItem)``
--------------------------------------------------------------------------
    Bases: ``ThreadSafeCurve``

    Provides a thread-safe curve with underlying ring buffers for the
    (x, y)-data. New readings are placed at the end (right-side) of the
    buffer, pushing out the oldest readings when the buffer has reached its
    maximum capacity (FIFO). Use methods ``append_data()`` and
    ``extend_data()`` to push in new data.

    See class ``ThreadSafeCurve`` for more details.

``class PlotCurve(capacity: int, linked_curve: pg.PlotDataItem)``
--------------------------------------------------------------------------
    Bases: ``ThreadSafeCurve``

    Provides a thread-safe curve with underlying regular array buffers
    for the (x, y)-data. Use method ``set_data()`` to set the data.

    See class ``ThreadSafeCurve`` for more details.
