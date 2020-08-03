Changelog
=========

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
