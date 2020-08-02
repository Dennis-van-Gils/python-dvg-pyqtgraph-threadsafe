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

                self.gw = pg.GraphicsLayoutWidget()
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
        window.tscurve_1.extendData([1, 2, 3, 4, 5], [10, 20, 30, 20, 10])

        # Draw the curve from out of the main thread
        window.tscurve_1.update()

        window.show()
        sys.exit(app.exec_())
"""
__author__ = "Dennis van Gils"
__authoremail__ = "vangils.dennis@gmail.com"
__url__ = "https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-threadsafe"
__date__ = "02-08-2020"
__version__ = "2.0.0"

from typing import Union, Tuple, List

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets as QtWid
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

        Intended multi-threaded operation: One or more threads push new data
        into the ``ThreadSafeCurve``-buffers. Another thread performs the GUI
        refresh by calling ``update()`` which will redraw the curve according
        to the current buffer contents.

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
                maximum capacity (FIFO). Use methods ``appendData()`` and
                ``extendData()`` to push in new data.

                When False, the (x, y)-data buffers are each a regular array
                buffer. Use method ``setData()`` to set the data.

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
        self.opts = self.curve.opts  # Use for read-only

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

    def appendData(self, x, y):
        """Append a single (x, y)-data point to the ring buffer.
        """
        if self._use_ringbuffer:
            locker = QtCore.QMutexLocker(self._mutex)
            self._buffer_x.append(x)
            self._buffer_y.append(y)
            locker.unlock()

    def extendData(self, x_list, y_list):
        """Extend the ring buffer with a list of (x, y)-data points.
        """
        if self._use_ringbuffer:
            locker = QtCore.QMutexLocker(self._mutex)
            self._buffer_x.extend(x_list)
            self._buffer_y.extend(y_list)
            locker.unlock()

    def setData(self, x_list, y_list):
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
        # Note: .setData() is also a fast operation and will internally emit
        # a PyQt signal to redraw the curve, once it has updated its data
        # members. That's why .setData() returns almost immediately, but the
        # curve still has to get redrawn by the Qt event engine, which will
        # happen automatically, eventually.
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

    @QtCore.pyqtSlot()
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

    def name(self):
        """Get the name of the curve.
        """
        return self.curve.name()

    def isVisible(self) -> bool:
        return self.curve.isVisible()

    def setVisible(self, state: bool = True):
        self.curve.setVisible(state)

    def setDownsampling(self, *args, **kwargs):
        """All arguments will be passed onto method
        ``pyqtgraph.PlotDataItem.setDownsampling()`` of the underlying curve.
        """
        self.curve.setDownsampling(*args, **kwargs)

    @property
    def size(self) -> Tuple[int, int]:
        """Number of elements currently contained in the underlying (x, y)-
        buffers of the curve. Note that this is not necessarily the number of
        elements of the currently drawn curve. Instead, it reflects the current
        sizes of the data buffers behind it that will be drawn onto screen by
        the next call to ``update()``.
        """
        # fmt: off
        locker = QtCore.QMutexLocker(self._mutex) # pylint: disable=unused-variable
        # fmt: on
        return (len(self._buffer_x), len(self._buffer_y))


# ------------------------------------------------------------------------------
#   Derived thread-safe curves
# ------------------------------------------------------------------------------


class HistoryChartCurve(ThreadSafeCurve):
    def __init__(self, capacity: int, linked_curve: pg.PlotDataItem):
        """Provides a thread-safe curve with underlying ring buffers for the
        (x, y)-data. New readings are placed at the end (right-side) of the
        buffer, pushing out the oldest readings when the buffer has reached its
        maximum capacity (FIFO). Use methods ``appendData()`` and
        ``extendData()`` to push in new data.

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
    def __init__(self, capacity: int, linked_curve: pg.PlotDataItem):
        """Provides a thread-safe curve with underlying ring buffers for the
        (x, y)-data. New readings are placed at the end (right-side) of the
        buffer, pushing out the oldest readings when the buffer has reached its
        maximum capacity (FIFO). Use methods ``appendData()`` and
        ``extendData()`` to push in new data.

        See class ``ThreadSafeCurve`` for more details.
        """
        super().__init__(
            capacity=capacity,
            linked_curve=linked_curve,
            shift_right_x_to_zero=False,
            use_ringbuffer=True,
        )


class PlotCurve(ThreadSafeCurve):
    def __init__(self, capacity: int, linked_curve: pg.PlotDataItem):
        """Provides a thread-safe curve with underlying regular array buffers
        for the (x, y)-data. Use method ``setData()`` to set the data.

        See class ``ThreadSafeCurve`` for more details.
        """
        super().__init__(
            capacity=capacity,
            linked_curve=linked_curve,
            shift_right_x_to_zero=False,
            use_ringbuffer=False,
        )


# ------------------------------------------------------------------------------
#   LegendSelect
# ------------------------------------------------------------------------------


class LegendSelect(QtWid.QWidget):
    def __init__(
        self,
        curves: List[Union[pg.PlotDataItem, ThreadSafeCurve]],
        hide_toggle_button: bool = False,
        box_bg_color: QtGui.QColor = QtGui.QColor(0, 0, 0),
        box_width: int = 40,
        box_height: int = 23,
        parent=None,
    ):
        """Create a legend of all passed curves with checkboxes to show or hide
        each curve. The legend ends with an push button to show or hide all
        curves in one go. The full set of GUI elements is contained in attribute
        ``grid`` of type ``PyQt5.QtWidget.QGridLayout`` to be added to your
        GUI.

        The initial visibility, name and pen of each curve will be retrieved
        from the members within the passed curves, i.e.:

            * ``curve.isVisible()``
            * ``curve.name()``
            * ``curve.opts["pen"]``

        Example grid:
            □ Curve 1 [ / ]
            □ Curve 2 [ / ]
            □ Curve 3 [ / ]
            [   toggle    ]

        Args:
            curves (``List[Union[pyqtgraph.PlotDataItem, ThreadSafeCurve]]``):
                List of ``pyqtgraph.PlotDataItem`` or ``ThreadSafeCurve`` to be
                controlled by the legend.

            hide_toggle_button (``bool``, optional):
                Default: False

            box_bg_color (``QtGui.QColor``, optional):
                Background color of the legend boxes.

                Default: ``QtGui.QColor(0, 0, 0)``

            box_width (``int``, optional):
                Default: 40

            box_height (``int``, optional):
                Default: 23

        Attributes:
            chkbs (``List[PyQt5.QtWidgets.QCheckbox]``):
                List of checkboxes to control the visiblity of each curve.

            painted_boxes (``List[PyQt5.QtWidgets.QWidget]``):
                List of painted boxes illustrating the pen of each curve

            qpbt_toggle (``PyQt5.QtWidgets.QPushButton``):
                Push button instance that toggles showing/hiding all curves in
                one go.

            grid (``PyQt5.QtWidgets.QGridLayout``):
                The full set of GUI elements combined into a grid to be added
                to your GUI.
        """
        super().__init__(parent=parent)

        self._curves = curves
        self.chkbs = list()
        self.painted_boxes = list()

        self.grid = QtWid.QGridLayout(spacing=1)
        for idx, curve in enumerate(self._curves):
            chkb = QtWid.QCheckBox(
                text=curve.name(),
                layoutDirection=QtCore.Qt.LeftToRight,
                checked=curve.isVisible(),
            )
            self.chkbs.append(chkb)
            # fmt: off
            chkb.clicked.connect(lambda: self._updateVisibility())  # pylint: disable=unnecessary-lambda
            # fmt: on

            painted_box = self.PaintedBox(
                pen=curve.opts["pen"],
                box_bg_color=box_bg_color,
                box_width=box_width,
                box_height=box_height,
            )
            self.painted_boxes.append(painted_box)

            p = {"alignment": QtCore.Qt.AlignLeft}
            self.grid.addWidget(chkb, idx, 0, **p)
            self.grid.addWidget(painted_box, idx, 1)
            self.grid.setColumnStretch(0, 0)
            self.grid.setColumnStretch(1, 0)  # Was (1, 1) before PyPi
            self.grid.setAlignment(QtCore.Qt.AlignTop)

        if not hide_toggle_button:
            self.qpbt_toggle = QtWid.QPushButton("toggle")
            self.grid.addItem(QtWid.QSpacerItem(0, 10), self.grid.rowCount(), 0)
            self.grid.addWidget(self.qpbt_toggle, self.grid.rowCount(), 0, 1, 3)
            self.qpbt_toggle.clicked.connect(self.toggle)

    @QtCore.pyqtSlot()
    def _updateVisibility(self):
        for idx, chkb in enumerate(self.chkbs):
            self._curves[idx].setVisible(chkb.isChecked())

    @QtCore.pyqtSlot()
    def toggle(self):
        # First : If any checkbox is unchecked  --> check all
        # Second: If all checkboxes are checked --> uncheck all
        any_unchecked = False
        for chkb in self.chkbs:
            if not chkb.isChecked():
                chkb.setChecked(True)
                any_unchecked = True

        if not any_unchecked:
            for chkb in self.chkbs:
                chkb.setChecked(False)

        self._updateVisibility()

    class PaintedBox(QtWid.QWidget):
        def __init__(
            self, pen, box_bg_color, box_width, box_height, parent=None
        ):
            super().__init__(parent=parent)

            self.pen = pen
            self.box_bg_color = box_bg_color

            self.setFixedWidth(box_width)
            self.setFixedHeight(box_height)

        def paintEvent(self, _event):
            w = self.width()
            h = self.height()
            x = 8  # offset line
            y = 6  # offset line

            painter = QtGui.QPainter()
            painter.begin(self)
            painter.fillRect(0, 0, w, h, self.box_bg_color)
            painter.setPen(self.pen)
            painter.drawLine(QtCore.QLine(x, h - y, w - x, y))
            painter.end()

