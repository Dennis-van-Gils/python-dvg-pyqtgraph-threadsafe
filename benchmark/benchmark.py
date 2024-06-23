#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Benchmark to test the ``pyqtgraph`` and ``dvg_pyqtgraph_threadsafe``
performance. You can experiment with different Python and PyQt versions, and
with enabling or disabling OpenGL hardware acceleration."""
__author__ = "Dennis van Gils"
__authoremail__ = "vangils.dennis@gmail.com"
__url__ = "https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-threadsafe"
# pylint: disable=wrong-import-position, missing-function-docstring
import os
import sys
import platform
from typing import List

# Constants
Fs = 10000
"""Sampling rate of the simulated data [Hz]"""
WORKER_DAQ_INTERVAL_MS = 10
"""Generate chunks of simulated data at this interval [ms]"""
CHART_DRAW_INTERVAL_MS = 20
"""Redraw the charts at this update interval [ms]"""
CHART_HISTORY_TIME = 10
"""History length of the charts [s]"""

# Benchmark constants
BENCH_INTERVAL_MS = 1000  # [ms]
BENCH_BUF_SIZE = 60  # Buffer size to calculate a moving average
BENCH_ITER_STARTUP = 10  # Number of iters to ignore at the start (settling)
BENCH_ITER_EXIT = 72  # Close app at this iter
BENCH_LOG_FILE = "log.txt"

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
    this_file = __file__.rsplit(os.sep, maxsplit=1)[-1]
    raise ImportError(
        f"{this_file} requires PyQt5, PyQt6, PySide2 or PySide6; "
        "none of these packages could be imported."
    )

# fmt: off
# pylint: disable=import-error, no-name-in-module
if QT_LIB == PYQT5:
    from PyQt5 import QtCore, QtWidgets as QtWid           # type: ignore
    from PyQt5.QtCore import pyqtSlot as Slot              # type: ignore
    from PyQt5.QtCore import pyqtSignal as Signal          # type: ignore
elif QT_LIB == PYQT6:
    from PyQt6 import QtCore, QtWidgets as QtWid           # type: ignore
    from PyQt6.QtCore import pyqtSlot as Slot              # type: ignore
    from PyQt6.QtCore import pyqtSignal as Signal          # type: ignore
elif QT_LIB == PYSIDE2:
    from PySide2 import QtCore, QtWidgets as QtWid         # type: ignore
    from PySide2.QtCore import Slot                        # type: ignore
    from PySide2.QtCore import Signal                      # type: ignore
elif QT_LIB == PYSIDE6:
    from PySide6 import QtCore, QtWidgets as QtWid         # type: ignore
    from PySide6.QtCore import Slot                        # type: ignore
    from PySide6.QtCore import Signal                      # type: ignore
# pylint: enable=import-error, no-name-in-module
# fmt: on

# pylint: disable=c-extension-no-member
QT_VERSION = (
    QtCore.QT_VERSION_STR if QT_LIB in (PYQT5, PYQT6) else QtCore.__version__
)
# pylint: enable=c-extension-no-member

# \end[Mechanism to support both PyQt and PySide]
# -----------------------------------------------

import psutil
import GPUtil
import numpy as np
import pyqtgraph as pg

PYQTGRAPH_MONKEYPATCH_APPLIED = False
try:
    import dvg_monkeypatch_pyqtgraph  # pylint: disable=unused-import
except ImportError:
    pass
else:
    if pg.__version__ == "0.11.0":
        PYQTGRAPH_MONKEYPATCH_APPLIED = True

TRY_USING_OPENGL = True
USING_OPENGL = False
if TRY_USING_OPENGL:
    try:
        import OpenGL.GL as gl  # pylint: disable=unused-import
    except ImportError:
        pass
    else:
        from OpenGL.version import __version__ as gl_version

        pg.setConfigOptions(useOpenGL=True)
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(enableExperimental=True)
        USING_OPENGL = True

# Logging
cur_date_time = QtCore.QDateTime.currentDateTime()
log_msg = (
    f"{'':-<{22}s}{cur_date_time.toString('yyMMdd_HHmmss')}\n"
    f"{'Python':9s} | {sys.version}\n"
    f"{QT_LIB:9s} | {QT_VERSION}\n"
    f"{'PyQtGraph':9s} | {pg.__version__}"
)
log_msg += " + monkeypatch\n" if PYQTGRAPH_MONKEYPATCH_APPLIED else "\n"
log_msg += f"{'PyOpenGL':9s} | "
log_msg += f"{gl_version}\n" if USING_OPENGL else "disabled\n"
log_msg += (
    f"{'Platform':9s} | {platform.platform()}\n"
    f"{'CPU':9s} | {platform.processor()}\n"
    f"{'GPU':9s} | {GPUtil.getGPUs()[0].name}\n"
    f"{'':-<{35}s}\n"
)
for line in log_msg:
    print(line, end="")
with open(BENCH_LOG_FILE, "a", encoding="UTF8") as f:
    f.writelines(log_msg)

from dvg_qdeviceio import QDeviceIO, DAQ_TRIGGER
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

# Keep track of the CPU load of this specific process
# `logical=False` for i7-11900H seems to match better what is reported by Win11
cpu_count = psutil.cpu_count(logical=True)
os_process = psutil.Process(os.getpid())
os_process.cpu_percent(interval=None)  # Prime the measurement

# ------------------------------------------------------------------------------
#   MainWindow
# ------------------------------------------------------------------------------


class MainWindow(QtWid.QWidget):
    def __init__(self, qdev: QDeviceIO, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.qdev = qdev
        self.qdev.signal_DAQ_updated.connect(self.update_GUI)

        self.setWindowTitle(f"Benchmark: {QT_LIB}, PyQtGraph {pg.__version__}")
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
#   BenchmarkDevice
# ------------------------------------------------------------------------------


class BenchmarkDevice(QtCore.QObject):
    """Simulates a device that keeps track of the benchmark stats and prints
    this to the terminal"""

    signal_benchmark_finished = Signal()

    def __init__(self):
        super().__init__()

        self.name = "Benchmark"
        self.is_alive = True

        self.iter = 0
        self.buf_fps = np.full(BENCH_BUF_SIZE, np.nan)
        self.buf_cpu_mem = np.full(BENCH_BUF_SIZE, np.nan)
        self.buf_cpu_load = np.full(BENCH_BUF_SIZE, np.nan)
        self.buf_gpu_load = np.full(BENCH_BUF_SIZE, np.nan)
        self.avg_fps = np.nan
        self.avg_cpu_mem = np.nan
        self.avg_cpu_load = np.nan
        self.avg_gpu_load = np.nan
        self.fps_min = np.nan
        self.fps_max = np.nan

    def measure_stats(self):
        # fps     : Instantaneous frames-per-second
        # cpu_load: Instantaneous CPU load of the Python process
        # cpu_mem : Instantaneous memory consumption of the Python process
        # gpu_load: Instantaneous system-wide GPU load
        fps = window.obtained_chart_rate_Hz  # Atomic, hence safe to access
        cpu_load = os_process.cpu_percent(interval=None) / cpu_count
        cpu_mem = os_process.memory_info().rss / 2**20
        gpu_load = GPUtil.getGPUs()[0].load * 100

        # FPS extrema
        if self.iter > BENCH_ITER_STARTUP:
            self.fps_min = np.nanmin((self.fps_min, fps))
            self.fps_max = np.nanmax((self.fps_max, fps))

        # Terminal info
        msg = (
            f"{self.iter:4d} | "
            f"{fps:4.1f} | {self.fps_min:4.1f} | {self.fps_max:4.1f} | "
            f"{cpu_mem:6.0f} | {cpu_load:4.1f} | {gpu_load:4.1f}"
        )

        # Moving average
        buf_idx = self.iter % BENCH_BUF_SIZE
        self.buf_fps[buf_idx] = fps
        self.buf_cpu_mem[buf_idx] = cpu_mem
        self.buf_cpu_load[buf_idx] = cpu_load
        self.buf_gpu_load[buf_idx] = gpu_load

        if self.iter >= BENCH_BUF_SIZE + BENCH_ITER_STARTUP:
            self.avg_fps = np.nanmean(self.buf_fps)
            self.avg_cpu_mem = np.nanmean(self.buf_cpu_mem)
            self.avg_cpu_load = np.nanmean(self.buf_cpu_load)
            self.avg_gpu_load = np.nanmean(self.buf_gpu_load)
            msg += (
                f"     {self.avg_fps:4.1f}{self.avg_cpu_mem:6.0f}"
                f" {self.avg_cpu_load:6.1f} {self.avg_gpu_load:6.1f}        "
            )
        else:
            msg += (
                "     waiting for moving average... "
                f"{(BENCH_BUF_SIZE + BENCH_ITER_STARTUP - self.iter):2d}"
            )

        # Terminal info
        print(msg, end="\r")

        # Time to exit? --> Print reStructuredText summary table
        if self.iter == BENCH_ITER_EXIT:
            COL_WIDTHS = (4, 10, 5, 5, 5, 8, 6, 6, 20)

            # Header
            print("\n")
            msg = ""
            for w in COL_WIDTHS:
                msg += f"{'':=<{w}s} "
            msg.rstrip()
            msg += (
                "\n"
                f"{'py':{COL_WIDTHS[0]}s} "
                f"{'QT_LIB':{COL_WIDTHS[1]}s} "
                f"{'<FPS>':{COL_WIDTHS[2]}s} "
                f"{'MIN':{COL_WIDTHS[3]}s} "
                f"{'MAX':{COL_WIDTHS[4]}s} "
                f"{'<RAM MB>':{COL_WIDTHS[5]}s} "
                f"{'<CPU%>':{COL_WIDTHS[6]}s} "
                f"{'<GPU%>':{COL_WIDTHS[7]}s} "
                f"{'pyqtgraph':{COL_WIDTHS[8]}s} "
                "\n"
            )
            for w in COL_WIDTHS:
                msg += f"{'':-<{w}s} "
            msg.rstrip()

            # Contents
            str_py = f"{sys.version_info.major:d}.{sys.version_info.minor:d}"
            msg += (
                "\n"
                f"{str_py:<{COL_WIDTHS[0]}s} "
                f"{QT_LIB:<{COL_WIDTHS[1]}s} "
                f"{self.avg_fps:<{COL_WIDTHS[2]}.1f} "
                f"{self.fps_min:<{COL_WIDTHS[3]}.1f} "
                f"{self.fps_max:<{COL_WIDTHS[4]}.1f} "
                f"{self.avg_cpu_mem:<{COL_WIDTHS[5]}.0f} "
                f"{self.avg_cpu_load:<{COL_WIDTHS[6]}.1f} "
                f"{self.avg_gpu_load:<{COL_WIDTHS[7]}.1f} "
                f"{pg.__version__:<{COL_WIDTHS[8]}s}"
            )
            if PYQTGRAPH_MONKEYPATCH_APPLIED:
                msg = msg.rstrip()
                msg += " + monkeypatch"

            # Logging
            for msg_line in msg:
                print(msg_line, end="")
            with open(BENCH_LOG_FILE, "a", encoding="UTF8") as f_log:
                f_log.writelines(msg)
                f_log.write("\n\n\n")

            self.signal_benchmark_finished.emit()

        self.iter += 1
        return True


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

    # BenchmarkDevice:
    #   Simulates a device that keeps track of the benchmark stats and prints
    #   this to the terminal.
    # QDeviceIO:
    #   Creates and manages a new thread for `benchmark_dev`. A worker will
    #   periodically activate `benchmark_dev` from out of this new thread.
    benchmark_dev = BenchmarkDevice()
    benchmark_qdev = QDeviceIO(benchmark_dev)
    benchmark_qdev.create_worker_DAQ(
        DAQ_trigger=DAQ_TRIGGER.INTERNAL_TIMER,
        DAQ_interval_ms=BENCH_INTERVAL_MS,
        DAQ_function=benchmark_dev.measure_stats,
    )

    print(
        "   # |  FPS |  MIN |  MAX | RAM MB | CPU% | GPU%     "
        "<FPS> <RAM> <CPU%> <GPU%>"
    )

    # Chart refresh timer
    timer_chart = QtCore.QTimer()
    timer_chart.setTimerType(QtCore.Qt.TimerType.PreciseTimer)
    timer_chart.timeout.connect(window.update_charts)

    # Start the workers and chart timer
    fake_qdev.start()
    benchmark_qdev.start()
    timer_chart.start(CHART_DRAW_INTERVAL_MS)

    # Program termination routine
    @Slot()
    def quit_benchmark():
        print("\n")
        benchmark_qdev.quit()
        app.quit()

    @Slot()
    def about_to_quit():
        print("\nAbout to quit")
        benchmark_qdev.quit()
        fake_qdev.quit()
        timer_chart.stop()

    # Start the main GUI event loop
    benchmark_dev.signal_benchmark_finished.connect(quit_benchmark)
    app.aboutToQuit.connect(about_to_quit)
    if QT_LIB in (PYQT5, PYSIDE2):
        sys.exit(app.exec_())
    else:
        sys.exit(app.exec())
