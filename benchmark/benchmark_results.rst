BENCHMARK
---------

We test different versions PyQtGraph and test different Qt
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
  3.1.6    5.15.2  5.15.2  6.4.0   6.3.2
  ======== ======= ======= ======= =======

* Display scaling is set to 100% in the OS.



RESULTS: Desktop *Onera*
------------------------

=========== ==================================
GPU         NVIDIA GeForce GTX 1070
CPU         AMD64 Family 23 Model 113 Stepping 0 (AMD Ryzen 5 3600)
Platform    Windows-10-10.0.19041-SP0
Python      3.10.6 | packaged by conda-forge | (main, Aug 22 2022, 20:29:51) [MSC v.1929 64 bit (AMD64)]
=========== ==================================

==== ========== ===== ===== ===== ======== ====== ====== ====================
py   QT_LIB     <FPS> MIN   MAX   <RAM MB> <CPU%> <GPU%> pyqtgraph
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
3.10 PyQt5      50.0  50.0  50.0  167      3.3    35.7   0.11.0 + monkeypatch
3.10 PyQt5      50.0  50.0  50.0  175      3.4    35.0   0.11.1              
3.10 PyQt5      50.0  50.0  50.0  183      4.0    34.8   0.12.4              
3.10 PyQt5      50.0  50.0  50.0  182      3.8    35.0   0.13.1              
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
3.10 PySide2    50.0  50.0  50.0  178      3.3    35.7   0.11.0 + monkeypatch
3.10 PySide2    50.0  49.0  50.1  185      3.2    35.8   0.11.1              
3.10 PySide2    50.0  50.0  50.1  194      4.2    34.3   0.12.4              
3.10 PySide2    50.0  50.0  50.1  193      4.0    35.9   0.13.1              
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
---- ---------- ----- ----- ----- -------- ------ ------ --------------------
3.10 PyQt6      50.0  50.0  50.0  239      4.5    33.8   0.12.4              
3.10 PyQt6      50.0  50.0  50.0  184      4.0    35.6   0.13.1              
==== ========== ===== ===== ===== ======== ====== ====== ====================
3.10 PySide6    50.0  49.9  50.3  196      4.5    35.8   0.12.4              
3.10 PySide6    50.0  50.0  50.1  195      4.1    36.5   0.13.1              
==== ========== ===== ===== ===== ======== ====== ====== ====================



CONCLUSION
----------

The PyQtGraph version can have an impact on drawing performance, though in the
system tested here it is not that apparent. Some integrated GPUs benefit from
using the older ``v0.11`` as it can reduce memory consumption and lead to
a higher sustained frame rate (tested but not yet turned into a table and shown
here). The older ``v0.11`` can only support *PyQt5* and *PySide2*, whereas
``v0.12+`` also supports *PyQt6* and *PySide6* which offer better display
scaling support.

| **Dennis van Gils**
| **12-10-2022**
|
| P.S. The ``v0.11.0`` monkeypatch and details can be found here https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-monkeypatch
