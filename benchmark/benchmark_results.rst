BENCHMARK
---------
We test different versions of Python and PyQtGraph and test different QT
libraries.

Two threads are set up. Thread one pushes every 10 ms 100 samples into a
ring buffer with a capacity of 300.000 samples. This thread has the upper
priority. The other lower thread takes care of plotting the 300.000
samples in the ring buffer at a max framerate of 50 fps.

We measure CPU & GPU load and memory consumption and check whether the max of
50 fps is reached for plotting.


CONDITIONS
----------
- Running: ``\demos\demo_pyqtgraph_threadsafe.py``
- Laptop_236G5FR3, Lenovo Thinkpad P15v Gen2
- Intel Core i7 11900H, 32 GB DDR4-3200, Win11 21H2
- GPU 0: Integrated Intel UHD
- GPU 1: NVidia Quadro T1200
- Display scaling set to 100%


OPENGL SETTINGS
---------------
::

  import pyqtgraph as pg
  import OpenGL.GL as gl
  pg.setConfigOptions(useOpenGL=True)
  pg.setConfigOptions(antialias=True)
  pg.setConfigOptions(enableExperimental=True)


RESULTS
-------

NOTE: These results are obtained *from the wrong GPU!* They are based on GPU 0,
which is the integrated graphics adapter (Intel UHD). We have to select GPU 1
as the preferred graphics processor in NVIDIA Control Panel to test the Quadro
T1200.

=============== ======= ======= ======= ======= ====================
Python & QT lib FPS     CPU     Mem     GPU     pyqtgraph
--------------- ------- ------- ------- ------- --------------------
.               fps     %       MB      %       .
--------------- ------- ------- ------- ------- --------------------
.               .       ±1      ±2      ±1      .
=============== ======= ======= ======= ======= ====================
py36pyqt5       50      6       152     72      0.11.0 + monkeypatch
py36pyqt5       50      7       203±20  76      0.11.1
--------------- ------- ------- ------- ------- --------------------
py36pyside2     50      6       163     72      0.11.0 + monkeypatch
py36pyside2     50      7       163     72      0.11.1
--------------- ------- ------- ------- ------- --------------------
py36pyqt6       not supported at all
--------------- ----------------------------------------------------
py36pyside6     not supported at all
--------------- ----------------------------------------------------
py39pyqt5       50      5       154     76      0.11.0 + monkeypatch
py39pyqt5       50      7       190+-20 75      0.11.1
py39pyqt5       ~30     4       228     43      0.12.4
--------------- ------- ------- ------- ------- --------------------
py39pyside2     50      6       160     72      0.11.0 + monkeypatch
py39pyside2     50      6       164     72      0.11.1
py39pyside2     ~30     5       232     43      0.12.4
--------------- ------- ------- ------- ------- --------------------
py39pyqt6       not supported                   0.11.1
--------------- ------------------------------- --------------------
py39pyside6     not supported                   0.11.1
--------------- ------------------------------- --------------------
py39pyqt6       ~30     4       228     44      0.12.4
py39pyside6     ~30     4       230     44      0.12.4
=============== ======= ======= ======= ======= ====================


CONCLUSION
----------

The PyQtGraph version seems to have a major impact on drawing performance. The
older ``v0.11`` seems superior in speed and memory, but can only support *PyQt5*
and *PySide2*, not *PyQt6* and *PySide6*. Whereas ``v0.12.4`` does support
*PyQt6* and *PySide6* but can't seem to match the performance of ``v0.11``.


| **Dennis van Gils**
| **16-09-2022**
|
| P.S. The ``v0.11.0`` monkeypatch and details can be found here https://github.com/Dennis-van-Gils/python-dvg-pyqtgraph-monkeypatch


TODO
----
Automate the benchmark using ``cpu_proc = self.proc.cpu_percent(interval=None) / self.cpu_count``
and https://github.com/anderskm/gputil. Also, all QT-libs can be installed in
a single environment and be specifically imported *before* ``import pyqtgraph``.
