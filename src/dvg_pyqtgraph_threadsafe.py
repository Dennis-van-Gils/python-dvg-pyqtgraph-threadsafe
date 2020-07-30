#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""*PyQtGraph library providing thread-safe plot curves with underlying (ring)
buffers:* ``HistoryChartCurve``, ``BufferedPlotCurve`` & ``PlotCurve``.

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
"""
__author__ = "Dennis van Gils"
__authoremail__ = "vangils.dennis@gmail.com"
__url__ = "https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-threadsafe"
__date__ = "30-07-2020"
__version__ = "1.0.0"

from typing import Tuple

import numpy as np
from PyQt5 import QtCore
import pyqtgraph as pg

from dvg_ringbuffer import RingBuffer


class ThreadSafeCurve(object):
    def __init__(
        self,
        capacity: int,
        linked_curve: pg.PlotDataItem,
        shift_right_x_to_zero: bool = False,
        use_ringbuffer: bool = True,
    ):
        """Provides the base class for a thread-safe plot *curve* to which
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
        """
        self.capacity = capacity
        self.curve = linked_curve
        self._shift_right_x_to_zero = shift_right_x_to_zero
        self._use_ringbuffer = use_ringbuffer
        self._mutex = QtCore.QMutex()  # To allow proper multithreading

        self.x_axis_divisor = 1
        self.y_axis_divisor = 1

        if self._use_ringbuffer:
            self._buffer_x = RingBuffer(capacity=capacity)
            self._buffer_y = RingBuffer(capacity=capacity)
        else:
            self._buffer_x = np.array([])
            self._buffer_y = np.array([])

        self._snapshot_x = [0]
        self._snapshot_y = [0]

        if self.curve is not None:
            # Performance boost: Do not plot data outside of visible range
            self.curve.clipToView = True

            # Default to no downsampling
            self.curve.setDownsampling(ds=1, auto=False, method="mean")

    def apply_downsampling(self, state: bool = True, ds=4):
        """Downsample the curve by using PyQtGraph's build-in method
        ``pyqtgraph.PlotDataItem.setDownsampling()``.
        """
        if self.curve is not None:
            if state:
                # Speed up plotting, needed for keeping the GUI responsive when
                # using large datasets
                self.curve.setDownsampling(ds=ds, auto=False, method="mean")
            else:
                self.curve.setDownsampling(ds=1, auto=False, method="mean")

    def append_data(self, x, y):
        """Append a single (x, y)-data point to the ring buffer.
        """
        if self._use_ringbuffer:
            locker = QtCore.QMutexLocker(self._mutex)
            self._buffer_x.append(x)
            self._buffer_y.append(y)
            locker.unlock()

    def extend_data(self, x_list, y_list):
        """Extend the ring buffer with a list of (x, y)-data points.
        """
        if self._use_ringbuffer:
            locker = QtCore.QMutexLocker(self._mutex)
            self._buffer_x.extend(x_list)
            self._buffer_y.extend(y_list)
            locker.unlock()

    def set_data(self, x_list, y_list):
        """Set the (x, y)-data of the regular array buffer.
        """
        if not self._use_ringbuffer:
            locker = QtCore.QMutexLocker(self._mutex)
            self._buffer_x = x_list
            self._buffer_y = y_list
            locker.unlock()

    def update(self):
        """Update the data behind the curve, based on the current contents of
        the buffer, and redraw the curve on screen.
        """

        # Create a snapshot of the buffered data. Fast operation.
        locker = QtCore.QMutexLocker(self._mutex)
        self._snapshot_x = np.copy(self._buffer_x)
        self._snapshot_y = np.copy(self._buffer_y)
        # print("numel x: %d, numel y: %d" %
        #      (self._snapshot_x.size, self._snapshot_y.size))
        locker.unlock()

        # Now update the data behind the curve and redraw it on screen.
        # Note: .setData() is a super fast operation and will internally emit
        # a PyQt signal to redraw the curve, once it has updated its data
        # members. That's why .setData() returns almost immediately, but the
        # curve still has to get drawn.
        if self.curve is not None:
            if (len(self._snapshot_x) == 0) or (
                np.alltrue(np.isnan(self._snapshot_y))
            ):
                self.curve.setData([], [])
            else:
                x_0 = self._snapshot_x[-1] if self._shift_right_x_to_zero else 0
                self.curve.setData(
                    (self._snapshot_x - x_0) / float(self.x_axis_divisor),
                    self._snapshot_y / float(self.y_axis_divisor),
                )

    def clear(self):
        """Clear the contents of the curve and redraw.
        """
        locker = QtCore.QMutexLocker(self._mutex)
        if self._use_ringbuffer:
            self._buffer_x.clear()
            self._buffer_y.clear()
        else:
            self._buffer_x = np.array([])
            self._buffer_y = np.array([])
        locker.unlock()

        self.update()

    def is_visible(self) -> bool:
        return self.curve.isVisible()

    def set_visible(self, state: bool = True):
        self.curve.setVisible(state)

    @property
    def size(self) -> Tuple[int, int]:
        """Number of elements currently contained in the underlying (x, y)-
        buffers of the curve. Note that this is not necessarily the number of
        elements of the currently drawn curve, but reflects the data buffer
        behind it that will be drawn onto screen by the next call to
        ``update()``.
        """
        # fmt: off
        locker = QtCore.QMutexLocker(self._mutex) # pylint: disable=unused-variable
        # fmt: on
        return (len(self._buffer_x), len(self._buffer_y))


# ------------------------------------------------------------------------------
#   Subclasses
# ------------------------------------------------------------------------------


class HistoryChartCurve(ThreadSafeCurve):
    def __init__(self, capacity: int, linked_curve: pg.PlotDataItem = None):
        """Provides a thread-safe curve with underlying ring buffers for the
        (x, y)-data. New readings are placed at the end (right-side) of the
        buffer, pushing out the oldest readings when the buffer has reached its
        maximum capacity (FIFO). Use methods ``append_data()`` and
        ``extend_data()`` to push in new data.

        The plotted x-data will be shifted such that the right-side is always
        set to 0. I.e., when ``x`` denotes time, the data is plotted backwards
        in time, hence the name *history* chart.

        See class ``ThreadSafeCurve`` for more details.
        """
        super().__init__(
            capacity=capacity,
            linked_curve=linked_curve,
            shift_right_x_to_zero=True,
            use_ringbuffer=True,
        )


class BufferedPlotCurve(ThreadSafeCurve):
    def __init__(self, capacity: int, linked_curve: pg.PlotDataItem = None):
        """Provides a thread-safe curve with underlying ring buffers for the
        (x, y)-data. New readings are placed at the end (right-side) of the
        buffer, pushing out the oldest readings when the buffer has reached its
        maximum capacity (FIFO). Use methods ``append_data()`` and
        ``extend_data()`` to push in new data.

        See class ``ThreadSafeCurve`` for more details.
        """
        super().__init__(
            capacity=capacity,
            linked_curve=linked_curve,
            shift_right_x_to_zero=False,
            use_ringbuffer=True,
        )


class PlotCurve(ThreadSafeCurve):
    def __init__(self, capacity: int, linked_curve: pg.PlotDataItem = None):
        """Provides a thread-safe curve with underlying regular array buffers
        for the (x, y)-data. Use method ``set_data()`` to set the data.

        See class ``ThreadSafeCurve`` for more details.
        """
        super().__init__(
            capacity=capacity,
            linked_curve=linked_curve,
            shift_right_x_to_zero=False,
            use_ringbuffer=False,
        )
