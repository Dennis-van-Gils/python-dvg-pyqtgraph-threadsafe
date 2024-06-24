Changelog
=========

3.4.0 (2024-06-24)
------------------
Code quality improvements:

* Using ``qtpy`` library instead of my own Qt5/6 mechanism
* Using f-strings
* Extended API and docstrings, like on `PlotManager`.
* Arguments `linked_curves` and `linked_plots` are hinted as `Sequence` instead
  of as `List`

Added support:

* Support for Numpy 2.0

3.3.0 (2023-02-27)
------------------
* Raise `ImportError` instead of general `Exception`

3.2.6 (2022-10-13)
------------------
* Added link to notes on use-case: DAQ

3.2.5 (2022-10-13)
------------------
* Minor edit: Using explicit arguments `x` and `y` to set the curve data and set
  the flag `skipFiniteCheck=True`. Both save (marginal) CPU time.

3.2.4 (2022-10-12)
------------------
* Bug fix: Snapshot creation checks if internal buffer is of type RingBuffer and
  casts to numpy.ndarray. This resolves an intermittent error where the
  `isfinite` boolean return array was operating as mask on the RingBuffer, which
  fails. The boolean return array now always operates on numpy.ndarray.
* Fix for external bug in `paintGL` of `pyqtgraph\graphicsItems\PlotCurveItem.py`:
  Added explicit check to ensure that the curve is only drawn when it has more
  than 1 point.
* Added benchmark running `python=3.10` and `pyqtgraph==0.13.1`

3.2.3 (2022-10-11)
------------------
* Fixed bug when using PyQt6: `QMessageBox.Yes` --> `QMessageBox.StandardButton.Yes`

3.2.2 (2022-09-18)
------------------
* Updated discussion on benchmarks
* The batch file for auto-creation of the conda environments found in the
  benchmark folder now uses the conda-forge channel.

3.2.1 (2022-09-17)
------------------
* Neater mechanism to support both PyQt and PySide
* Added benchmarks
* Improved demos

3.2.0 (2022-09-13)
------------------
* Added support for PyQt5, PyQt6, PySide2 and PySide6 as suggested via a pull
  request by Mathijs van Gorcum (https://github.com/mvgorcum).

3.1.0 (2021-05-10)
------------------
* Removed redundant argument ``capacity`` from init ``PlotCurve()``. It is
  not using a ringbuffer and, hence, does not need a capacity.

3.0.1 (2020-08-07)
------------------
Bug-fixes:

* The use of ``typing.TypedDict`` broke support under Python 3.6
  and 3.7. Fixed by conditional import ``typing_extensions``.
* Curve plotting was broken when ``setClipToView(True)`` and the curve
  data extended past the viewbox limits, when not using OpenGL. The cause was
  my incorrect calculation of ``connect``. Fixed by commenting out ``connect``
  again. Curves will now show continuously (linear interpolation) whenever a NaN
  is encountered, instead of as correctly fragmented. That's acceptable.

3.0.0 (2020-08-07)
------------------
* Renamed parameter ``LegendSelect.curves`` to
  ``LegendSelect.linked_curves``
* Changed base of class ``LegendSelect()`` from ``QWidget`` to ``QObject``
* Added class ``PlotManager()``

2.0.1 (2020-08-03)
------------------
* Workaround: ``PyQt5 >= 5.12.3`` causes a bug in ``PyQtGraph`` where a
  curve won't render if it contains NaNs (but only in the case when OpenGL is
  disabled). The curve will now be displayed correctly, i.e., fragmented
  whenever a NaN is encountered. When OpenGL is enabled, linear interpolation
  will occur at the gaps as per ``pyqtgraph.plotCurveItem.paintGL()``.

2.0.0 (2020-08-02)
------------------
* Method names are now conform the ``PyQtGraph`` naming style. I.e.
  ``setData()`` vs. ``set_data()``, etc.
* The default values of ``PyQtGraph`` are no longer being overwritten.
* Added class ``LegendSelect``

1.0.0 (2020-07-30)
------------------
* First release on PyPI
