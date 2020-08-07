#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import numpy as np
from PyQt5 import QtCore
from PyQt5 import QtWidgets as QtWid
import pyqtgraph as pg

try:
    from dvg_qdeviceio import QDeviceIO
except ImportError:
    print("This demo requires `dvg-qdeviceio`. It can be installed with:")
    print("  pip install dvg-qdeviceio")
    sys.exit(0)

from dvg_pyqtgraph_threadsafe import (
    HistoryChartCurve,
    BufferedPlotCurve,
    LegendSelect,
    PlotManager,
)

USE_OPENGL = True
if USE_OPENGL:
    print("OpenGL acceleration: Enabled")
    pg.setConfigOptions(useOpenGL=True)
    pg.setConfigOptions(antialias=True)
    pg.setConfigOptions(enableExperimental=True)

# Global pyqtgraph configuration
# pg.setConfigOptions(leftButtonPan=False)
pg.setConfigOption("foreground", "#EEE")

# Constants
Fs = 10000  # Sampling rate of the simulated data [Hz]
WORKER_DAQ_INTERVAL_MS = round(1000 / 100)  # [ms]
CHART_DRAW_INTERVAL_MS = round(1000 / 50)  # [ms]
CHART_HISTORY_TIME = 10  # 10 [s]

# ------------------------------------------------------------------------------
#   MainWindow
# ------------------------------------------------------------------------------


class MainWindow(QtWid.QWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.setGeometry(350, 50, 1200, 660)
        self.setWindowTitle("Demo: dvg_pyqtgraph_threadsafe")

        # Keep track of the obtained chart refresh rate
        self.obtained_chart_rate_Hz = np.nan
        self.qet_chart = QtCore.QElapsedTimer()
        self.chart_rate_accumulator = 0

        # Pause/unpause charts
        self.paused = False

        # GraphicsLayoutWidget
        self.gw = pg.GraphicsLayoutWidget()

        p = {"color": "#EEE", "font-size": "12pt"}
        self.plot_1 = self.gw.addPlot()
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

        self.plot_2 = self.gw.addPlot()
        # self.plot_2.setClipToView(True)  # Note: Do not enable clip for a Lissajous. Clip only works well on uniformly monotic x-data.
        self.plot_2.showGrid(x=1, y=1)
        self.plot_2.setTitle("BufferedPlotCurve: Lissajous")
        self.plot_2.setLabel("bottom", text="x", **p)
        self.plot_2.setLabel("left", text="y", **p)
        self.plot_2.setRange(
            xRange=[-1.1, 1.1], yRange=[-1.1, 1.1], disableAutoRange=True,
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

        self.tscurves = [
            self.tscurve_1,
            self.tscurve_2,
            self.tscurve_3,
        ]

        # Extra marker to indicate tracking position of Lissajous curve
        self.lissajous_marker = self.plot_2.plot(
            pen=None,
            symbol="o",
            symbolPen=None,
            symbolBrush=pg.mkBrush([255, 30, 180]),
            symbolSize=16,
        )

        # 'Obtained rates'
        self.qlbl_DAQ_rate = QtWid.QLabel("")
        self.qlbl_DAQ_rate.setAlignment(QtCore.Qt.AlignRight)
        self.qlbl_DAQ_rate.setMinimumWidth(50)
        self.qlbl_chart_rate = QtWid.QLabel("")
        self.qlbl_chart_rate.setAlignment(QtCore.Qt.AlignRight)
        self.qlbl_num_points = QtWid.QLabel("")
        self.qlbl_num_points.setAlignment(QtCore.Qt.AlignRight)

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
        grid_rates.setAlignment(QtCore.Qt.AlignTop)
        # fmt: on

        # 'Legend'
        legend = LegendSelect(linked_curves=self.tscurves)
        qgrp_legend = QtWid.QGroupBox("LegendSelect")
        qgrp_legend.setLayout(legend.grid)

        # Update `number of points drawn` at each click `show/hide curve`
        for chkb in legend.chkbs:
            chkb.clicked.connect(self.update_num_points_drawn)

        # `PlotManager`
        self.qpbt_pause_chart = QtWid.QPushButton("Pause", checkable=True)
        self.qpbt_pause_chart.clicked.connect(self.process_qpbt_pause_chart)

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
        self.plot_manager.add_clear_button(self.tscurves)
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

    @QtCore.pyqtSlot()
    def process_qpbt_clear_chart(self):
        str_msg = "Are you sure you want to clear the chart?"
        reply = QtWid.QMessageBox.warning(
            window,
            "Clear chart",
            str_msg,
            QtWid.QMessageBox.Yes | QtWid.QMessageBox.No,
            QtWid.QMessageBox.No,
        )

        if reply == QtWid.QMessageBox.Yes:
            for tscurve in self.tscurves:
                tscurve.clear()

    @QtCore.pyqtSlot()
    def process_qpbt_pause_chart(self):
        if self.paused:
            self.qpbt_pause_chart.setText("Pause")
            self.paused = False
        else:
            self.qpbt_pause_chart.setText("Paused")
            self.paused = True

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

        self.qlbl_num_points.setText("%s" % f"{(num_points):,}")

    @QtCore.pyqtSlot()
    def update_curves(self):
        for tscurve in self.tscurves:
            tscurve.update()

        if len(self.tscurve_3.curve.xData) > 0:
            self.lissajous_marker.setData(
                [self.tscurve_3.curve.xData[-1]],
                [self.tscurve_3.curve.yData[-1]],
            )

    @QtCore.pyqtSlot()
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
            self.qlbl_chart_rate.setText("%.1f" % self.obtained_chart_rate_Hz)
            self.update_num_points_drawn()
            self.update_curves()

    @QtCore.pyqtSlot()
    def update_GUI(self):
        self.qlbl_DAQ_rate.setText("%.1f" % qdev.obtained_DAQ_rate_Hz)


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


@QtCore.pyqtSlot()
def about_to_quit():
    qdev.quit()
    timer_chart.stop()


def DAQ_function():
    if window.tscurve_1.size[0] == 0:
        x_0 = 0
    else:
        # Pick up the previously last phase of the sine
        x_0 = window.tscurve_1._buffer_x[-1]  # pylint: disable=protected-access

    x = (1 + np.arange(WORKER_DAQ_INTERVAL_MS * Fs / 1e3)) / Fs + x_0
    y_sin = np.sin(2 * np.pi * 0.5 * np.unwrap(x))
    y_cos = np.cos(2 * np.pi * 0.09 * np.unwrap(x))

    window.tscurve_1.extendData(x, y_sin)
    window.tscurve_2.extendData(x, y_cos)
    window.tscurve_3.extendData(y_sin, y_cos)

    return True


# ------------------------------------------------------------------------------
#   Main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    app = QtWid.QApplication(sys.argv)
    app.aboutToQuit.connect(about_to_quit)

    window = MainWindow()

    # Fake a device that generates data at a sampling rate of `Fs` Hz. The
    # data gets generated and transferred to our HistoryChartCurve-instance from
    # out of a separate thread. This is taken care of by QDeviceIO.
    class FakeDevice:
        def __init__(self):
            self.name = "FakeDevice"
            self.is_alive = True

    qdev = QDeviceIO(dev=FakeDevice())
    qdev.create_worker_DAQ(
        DAQ_interval_ms=WORKER_DAQ_INTERVAL_MS, DAQ_function=DAQ_function
    )
    qdev.signal_DAQ_updated.connect(window.update_GUI)
    qdev.start()

    # Chart refresh timer
    timer_chart = QtCore.QTimer(timerType=QtCore.Qt.PreciseTimer)
    timer_chart.timeout.connect(window.update_charts)
    timer_chart.start(CHART_DRAW_INTERVAL_MS)

    window.show()
    sys.exit(app.exec_())
