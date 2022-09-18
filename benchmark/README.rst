Running the benchmark
=====================

A single benchmark can be run by calling::

  python benchmark.py [optional argument]
  
where the optional argument can be ``PyQt5``, ``PyQt6``,
``PySide2`` or ``PySide6`` to enforce using a specific
Python Qt library.

It is possible to have PyQt5, PyQt6, PySide2 and PySide6 *all* installed
in the same python environment.

Automated benchmarks
====================

If you use Anaconda Python then I have scripts available to set up the
Python environments for benchmarking, see `<create_conda_envs.bat>`_.
With this set up, you can run the full benchmark matrix found in
`<automate_benchmarks.bat>`_.

GPU load
========

If you have an NVidia GPU then the benchmark will report the system-wide
GPU load. Any other card will result in a reading of 0%. 

Graphics card preference
========================

When your system has both an integrated GPU and a dedicated one, please make
sure to tell the OS to favour the correct GPU.

In Windows you must go to the 'Graphics settings' configuration page, add an
entry for ``python.exe`` for each of the conda environments *py36bench* and
*py39bench*, usually located at ``%USERPROFILE%\anaconda3\envs``. Then click on
the new ``python.exe`` entry in the list and select the correct GPU.

Desktop scaling
===============

For fair comparisons between Qt5 and Qt6 you must ensure that the desktop
scaling is set to 100%. This is because Qt5 does not scale the application
window according to the display scaling correctly, whereas Qt6 will.
