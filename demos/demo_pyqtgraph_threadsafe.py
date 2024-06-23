#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo to showcase the `dvg_pyqtgraph_threadsafe` library."""
__author__ = "Dennis van Gils"
__authoremail__ = "vangils.dennis@gmail.com"
__url__ = "https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-threadsafe"
__date__ = "23-06-2024"
# pylint: disable=wrong-import-position, missing-function-docstring

import sys
from typing import List

import qtpy
from qtpy import QtCore, QtWidgets as QtWid
from qtpy.QtCore import Slot  # type: ignore

import pyqtgraph as pg
import numpy as np

print("-" * 23)
print(f"{'Python':9s} | {sys.version}")
print(f"{qtpy.API_NAME:9s} | {qtpy.QT_VERSION}")  # type: ignore
print(f"{'PyQtGraph':9s} | {pg.__version__}", end="")

try:
    import dvg_monkeypatch_pyqtgraph  # pylint: disable=unused-import
except ImportError:
    pass
else:
    if pg.__version__ == "0.11.0":
        print(" + dvg_monkeypatch_pyqtgraph", end="")
print()

TRY_USING_OPENGL = True
if TRY_USING_OPENGL:
    try:
        import OpenGL.GL as gl  # pylint: disable=unused-import
    except ImportError:
        print("OpenGL acceleration: Disabled")
        print("To install: `conda install pyopengl` or `pip install pyopengl`")
    else:
        from OpenGL.version import __version__ as gl_version

        print(f"{'PyOpenGL':9s} | {gl_version}")
        pg.setConfigOptions(useOpenGL=True)
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(enableExperimental=True)

print("-" * 23)

try:
    from dvg_qdeviceio import QDeviceIO, DAQ_TRIGGER
except ImportError:
    print("This demo requires `dvg-qdeviceio`. It can be installed with:")
    print("  pip install dvg-qdeviceio")
    sys.exit(0)

from dvg_pyqtgraph_threadsafe import (
    ThreadSafeCurve,
    HistoryChartCurve,
    BufferedPlotCurve,
    LegendSelect,
    PlotManager,
)

# Global pyqtgraph configuration
# pg.setConfigOptions(leftButtonPan=False)
pg.setConfigOption("foreground", "#EEE")

# Constants
Fs = 10000
"""Sampling rate of the simulated data [Hz]"""
WORKER_DAQ_INTERVAL_MS = round(1000 / 100)
"""Generate chunks of simulated data at this interval [ms]"""
CHART_DRAW_INTERVAL_MS = round(1000 / 50)
"""Redraw the charts at this update interval [ms]"""
CHART_HISTORY_TIME = 10
"""History length of the charts [s]"""

# ------------------------------------------------------------------------------
#   MainWindow
# ------------------------------------------------------------------------------


class MainWindow(QtWid.QWidget):
    def __init__(self, qdev: QDeviceIO, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.qdev = qdev
        self.qdev.signal_DAQ_updated.connect(self.update_GUI)

        self.setWindowTitle("Demo: dvg_pyqtgraph_threadsafe")
        self.setGeometry(350, 50, 1200, 660)

        # Keep track of the obtained chart refresh rate
        self.obtained_chart_rate_Hz = np.nan
        self.qet_chart = QtCore.QElapsedTimer()
        self.chart_rate_accumulator = 0

        # Pause/unpause charts
        self.paused = False

        # GraphicsLayoutWidget
        self.gw = pg.GraphicsLayoutWidget()

        p = {"color": "#EEE", "font-size": "12pt"}
        self.plot_1: pg.PlotItem = self.gw.addPlot()
        self.plot_1.setClipToView(True)
        self.plot_1.showGrid(x=1, y=1)
        self.plot_1.setTitle("HistoryChartCurve")
        self.plot_1.setLabel("bottom", text="history (sec)", **p)
        self.plot_1.setLabel("left", text="amplitude", **p)
        self.plot_1.setRange(
            xRange=[-1.04 * CHART_HISTORY_TIME, CHART_HISTORY_TIME * 0.04],
            yRange=[-1.1, 1.1],
            disableAutoRange=True,
        )

        self.plot_2: pg.PlotItem = self.gw.addPlot()
        # Note: Do not enable clip for a Lissajous. Clip only works well on
        # uniformly monotic x-data.
        # self.plot_2.setClipToView(True)  # Commented out
        self.plot_2.showGrid(x=1, y=1)
        self.plot_2.setTitle("BufferedPlotCurve: Lissajous")
        self.plot_2.setLabel("bottom", text="x", **p)
        self.plot_2.setLabel("left", text="y", **p)
        self.plot_2.setRange(
            xRange=[-1.1, 1.1],
            yRange=[-1.1, 1.1],
            disableAutoRange=True,
        )

        capacity = round(CHART_HISTORY_TIME * Fs)
        self.tscurve_1 = HistoryChartCurve(
            capacity=capacity,
            linked_curve=self.plot_1.plot(
                pen=pg.mkPen(color=[255, 30, 180], width=3), name="wave 1"
            ),
        )
        self.tscurve_2 = HistoryChartCurve(
            capacity=capacity,
            linked_curve=self.plot_1.plot(
                pen=pg.mkPen(color=[0, 255, 255], width=3), name="wave 2"
            ),
        )
        self.tscurve_3 = BufferedPlotCurve(
            capacity=capacity,
            linked_curve=self.plot_2.plot(
                pen=pg.mkPen(color=[255, 255, 90], width=3), name="Lissajous"
            ),
        )

        self.tscurves: List[ThreadSafeCurve] = [
            self.tscurve_1,
            self.tscurve_2,
            self.tscurve_3,
        ]
        """List containing all used ThreadSafeCurves instances."""

        # Extra marker to indicate tracking position of Lissajous curve
        self.lissajous_marker = self.plot_2.plot(
            pen=None,
            symbol="o",
            symbolPen=None,
            symbolBrush=pg.mkBrush([255, 30, 180]),
            symbolSize=16,
        )

        # Obtained rates
        self.qlbl_DAQ_rate = QtWid.QLabel("")
        self.qlbl_DAQ_rate.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.qlbl_DAQ_rate.setMinimumWidth(50)
        self.qlbl_chart_rate = QtWid.QLabel("")
        self.qlbl_chart_rate.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.qlbl_num_points = QtWid.QLabel("")
        self.qlbl_num_points.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        # fmt: off
        grid_rates = QtWid.QGridLayout()
        grid_rates.addWidget(QtWid.QLabel("DAQ:")  , 0, 0)
        grid_rates.addWidget(self.qlbl_DAQ_rate    , 0, 1)
        grid_rates.addWidget(QtWid.QLabel("Hz")    , 0, 2)
        grid_rates.addWidget(QtWid.QLabel("chart:"), 1, 0)
        grid_rates.addWidget(self.qlbl_chart_rate  , 1, 1)
        grid_rates.addWidget(QtWid.QLabel("Hz")    , 1, 2)
        grid_rates.addWidget(QtWid.QLabel("drawn:"), 2, 0)
        grid_rates.addWidget(self.qlbl_num_points  , 2, 1)
        grid_rates.addWidget(QtWid.QLabel("pnts")  , 2, 2)
        grid_rates.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        # fmt: on

        # Legend
        legend = LegendSelect(linked_curves=self.tscurves)
        qgrp_legend = QtWid.QGroupBox("LegendSelect")
        qgrp_legend.setLayout(legend.grid)

        # Update `number of points drawn` at each click `show/hide curve`
        for chkb in legend.chkbs:
            chkb.clicked.connect(self.update_num_points_drawn)

        # Plot manager
        self.qpbt_pause_chart = QtWid.QPushButton("Pause")
        self.qpbt_pause_chart.setCheckable(True)
        # pylint: disable=unnecessary-lambda
        self.qpbt_pause_chart.clicked.connect(
            lambda checked: self.process_qpbt_pause_chart(checked)
        )
        # pylint: enable=unnecessary-lambda

        self.plot_manager = PlotManager(parent=self)
        self.plot_manager.grid.addWidget(self.qpbt_pause_chart, 0, 0, 1, 2)
        self.plot_manager.grid.addItem(QtWid.QSpacerItem(0, 10), 1, 0)
        self.plot_manager.add_autorange_buttons(
            linked_plots=[self.plot_1, self.plot_2]
        )
        self.plot_manager.add_preset_buttons(
            linked_plots=[self.plot_1],
            linked_curves=[self.tscurve_1, self.tscurve_2],
            presets=[
                {
                    "button_label": "0.100",
                    "x_axis_label": "history (msec)",
                    "x_axis_divisor": 1e-3,
                    "x_axis_range": (-101, 0),
                },
                {
                    "button_label": "0:05",
                    "x_axis_label": "history (sec)",
                    "x_axis_divisor": 1,
                    "x_axis_range": (-5.05, 0),
                },
                {
                    "button_label": "0:10",
                    "x_axis_label": "history (sec)",
                    "x_axis_divisor": 1,
                    "x_axis_range": (-10.1, 0),
                },
            ],
        )
        self.plot_manager.add_clear_button(linked_curves=self.tscurves)
        self.plot_manager.perform_preset(1)

        qgrp_plotmgr = QtWid.QGroupBox("PlotManager")
        qgrp_plotmgr.setLayout(self.plot_manager.grid)

        # Round up right panel
        vbox = QtWid.QVBoxLayout()
        vbox.addLayout(grid_rates)
        vbox.addWidget(qgrp_legend)
        vbox.addWidget(qgrp_plotmgr, stretch=0)
        vbox.addStretch()

        # Round up frame
        hbox = QtWid.QHBoxLayout()
        hbox.addWidget(self.gw, 1)
        hbox.addLayout(vbox, 0)

        # -------------------------
        #   Round up full window
        # -------------------------

        vbox = QtWid.QVBoxLayout(self)
        vbox.addLayout(hbox, stretch=1)

    # --------------------------------------------------------------------------
    #   Handle controls
    # --------------------------------------------------------------------------

    @Slot(bool)
    def process_qpbt_pause_chart(self, checked: bool):
        self.paused = checked
        self.qpbt_pause_chart.setText("Paused" if checked else "Pause")

    def update_num_points_drawn(self):
        # Keep track of the number of drawn points
        num_points = 0
        for tscurve in self.tscurves:
            if tscurve.isVisible():
                num_points += (
                    0
                    if tscurve.curve.xData is None
                    else len(tscurve.curve.xData)
                )

        self.qlbl_num_points.setText(f"{(num_points):,}")

    @Slot()
    def update_curves(self):
        for tscurve in self.tscurves:
            tscurve.update()

        if (
            self.tscurve_3.curve.xData is not None
            and self.tscurve_3.curve.yData is not None
        ):
            if len(self.tscurve_3.curve.xData) > 0:
                self.lissajous_marker.setData(
                    [self.tscurve_3.curve.xData[-1]],
                    [self.tscurve_3.curve.yData[-1]],
                )

    @Slot()
    def update_charts(self):
        # Keep track of the obtained chart rate
        if not self.qet_chart.isValid():
            self.qet_chart.start()
        else:
            self.chart_rate_accumulator += 1
            dT = self.qet_chart.elapsed()

            if dT >= 1000:  # Evaluate every N elapsed milliseconds
                self.qet_chart.restart()
                try:
                    self.obtained_chart_rate_Hz = (
                        self.chart_rate_accumulator / dT * 1e3
                    )
                except ZeroDivisionError:
                    self.obtained_chart_rate_Hz = np.nan

                self.chart_rate_accumulator = 0

        # Update curves
        if not self.paused:
            self.qlbl_chart_rate.setText(f"{self.obtained_chart_rate_Hz:.1f}")
            self.update_num_points_drawn()
            self.update_curves()

    @Slot()
    def update_GUI(self):
        self.qlbl_DAQ_rate.setText(f"{self.qdev.obtained_DAQ_rate_Hz:.1f}")


# ------------------------------------------------------------------------------
#   FakeDevice
# ------------------------------------------------------------------------------


class FakeDevice:
    """Simulates a data acquisition (DAQ) device that will generate data at a
    fixed sampling rate.
    """

    def __init__(
        self,
    ):
        self.name = "FakeDevice"
        self.is_alive = True

        self.block_size = int(np.round(WORKER_DAQ_INTERVAL_MS * Fs / 1e3))
        self.data_x = np.zeros(self.block_size)
        self.data_y_1 = np.zeros(self.block_size)
        self.data_y_2 = np.zeros(self.block_size)

        self.prev_x_value = 0
        """Remember the phase of the previously generated data."""

    def generate_data(self):
        x = (1 + np.arange(self.block_size)) / Fs + self.prev_x_value
        self.prev_x_value = x[-1]

        self.data_x = x
        self.data_y_1 = np.sin(2 * np.pi * 0.5 * np.unwrap(x))
        self.data_y_2 = np.cos(2 * np.pi * 0.09 * np.unwrap(x))


# ------------------------------------------------------------------------------
#   Main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Create QT application
    app = QtWid.QApplication(sys.argv)

    # FakeDevice:
    #   Simulates a data acquisition (DAQ) device that will generate data at a
    #   fixed sampling rate.
    fake_dev = FakeDevice()

    # QDeviceIO:
    #   Creates and manages a new thread for `fake_dev`. A worker will
    #   periodically make `fake_dev` generate new data from out of this new
    #   thread. The worker is called `Worker_DAQ`.
    fake_qdev = QDeviceIO(fake_dev)

    def DAQ_function() -> bool:
        """Data-acquisition (DAQ) routine to be run every time `Worker_DAQ`
        is triggered. In this example we will set up `Worker_DAQ` to trigger at
        a fixed interval of an internal timer."""

        # Simulate new data coming in
        fake_dev.generate_data()

        # Add readings to the ThreadSafeCurves. This can be done from out of
        # another thread like this one.
        window.tscurve_1.extendData(fake_dev.data_x, fake_dev.data_y_1)
        window.tscurve_2.extendData(fake_dev.data_x, fake_dev.data_y_2)
        window.tscurve_3.extendData(fake_dev.data_y_1, fake_dev.data_y_2)

        # Must return True to indicate all went successful
        return True

    fake_qdev.create_worker_DAQ(
        DAQ_trigger=DAQ_TRIGGER.INTERNAL_TIMER,
        DAQ_interval_ms=WORKER_DAQ_INTERVAL_MS,
        DAQ_function=DAQ_function,
    )

    # Create the GUI
    window = MainWindow(qdev=fake_qdev)
    window.show()

    # Chart refresh timer
    timer_chart = QtCore.QTimer()
    timer_chart.setTimerType(QtCore.Qt.TimerType.PreciseTimer)
    timer_chart.timeout.connect(window.update_charts)

    # Start the worker and chart timer
    fake_qdev.start()
    timer_chart.start(CHART_DRAW_INTERVAL_MS)

    # Program termination routine
    @Slot()
    def about_to_quit():
        print("\nAbout to quit")
        fake_qdev.quit()
        timer_chart.stop()

    # Start the main GUI event loop
    app.aboutToQuit.connect(about_to_quit)
    sys.exit(app.exec())
