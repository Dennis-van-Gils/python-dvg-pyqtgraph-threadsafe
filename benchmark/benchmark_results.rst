BENCHMARK
---------

We test different versions of Python and PyQtGraph and test different Qt
libraries. We only focus on the 2D line plot capabilities with OpenGL
acceleration enabled.

Two threads are set up. Thread one pushes every 10 ms 100 samples into a
ring buffer with a capacity of 300.000 samples. This thread has the upper
priority. The other lower thread takes care of plotting the 300.000
samples in the ring buffer at a max framerate of 50 fps.

We measure CPU & GPU load and memory consumption and check whether the max of
50 fps is maintained for plotting.



CONDITIONS
----------

* OpenGL acceleration is enabled for all tests with the following options set::

    import pyqtgraph as pg
    pg.setConfigOptions(useOpenGL=True)
    pg.setConfigOptions(antialias=True)
    pg.setConfigOptions(enableExperimental=True)

* Versions

  ======== ======= ======= ======= =======
  PyOpenGL PyQt5   PySide2 PyQt6   PySide6
  -------- ------- ------- ------- -------
  3.1.6    5.15.2  5.15.2  6.3.1   6.3.2
  ======== ======= ======= ======= =======

* Display scaling is set to 100% in the OS.



RESULTS: Desktop *Onera*
------------------------

=========== ==================================
GPU         NVIDIA GeForce GTX 1070
CPU         AMD64 Family 23 Model 113 Stepping 0 (AMD Ryzen 5 3600)
Platform    Windows-10-10.0.19041-SP0
Python      3.6.15 (default, Dec  3 2021, 18:25:24) [MSC v.1916 64 bit (AMD64)]
Python      3.9.13 | packaged by conda-forge | (main, May 27 2022, 16:51:29) [MSC v.1929 64 bit (AMD64)]
=========== ==================================

==== ========== ===== ===== ===== ======== ====== ====== ====================
py   QT_LIB     <FPS> MIN   MAX   <RAM MB> <CPU%> <GPU%> pyqtgraph
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
3.6  PyQt5      50.0  50.0  50.0  151      3.7    35.1   0.11.0 + monkeypatch
3.6  PyQt5      50.0  50.0  50.0  158      4.6    35.8   0.11.1              
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
3.6  PySide2    50.0  50.0  50.0  162      3.8    35.1   0.11.0 + monkeypatch
3.6  PySide2    50.0  50.0  50.0  165      4.4    36.1   0.11.1              
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
3.9  PyQt5      50.0  50.0  50.0  166      3.1    35.7   0.11.0 + monkeypatch
3.9  PyQt5      50.0  50.0  50.1  175      3.5    35.9   0.11.1              
3.9  PyQt5      50.0  49.0  50.1  184      4.3    33.8   0.12.4              
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
3.9  PySide2    50.0  50.0  50.1  178      3.3    36.3   0.11.0 + monkeypatch
3.9  PySide2    50.0  50.0  50.0  184      3.2    36.2   0.11.1              
3.9  PySide2    50.0  49.1  50.0  195      4.7    34.6   0.12.4              
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
3.9  PyQt6      50.0  50.0  50.1  186      4.2    35.6   0.12.4              
3.9  PySide6    50.0  49.0  50.1  197      4.3    34.9   0.12.4              
==== ========== ===== ===== ===== ======== ====== ====== ====================



CONCLUSION
----------

The PyQtGraph version can have an impact on drawing performance, though in the
system tested here it is not that apparent. Some integrated GPUs benefit from
using the older ``v0.11`` as it can reduce memory consumption and lead to
a higher sustained frame rate (tested but not yet turned into a table and shown
here). The older ``v0.11`` can only support *PyQt5* and *PySide2*, whereas
``v0.12.4`` also supports *PyQt6* and *PySide6* which offer better display
scaling support.

| **Dennis van Gils**
| **18-09-2022**
|
| P.S. The ``v0.11.0`` monkeypatch and details can be found here https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-monkeypatch
