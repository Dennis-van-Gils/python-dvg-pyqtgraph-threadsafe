Graphics card preference
========================

When your system has both an integrated GPU and an external one, please make
sure to tell the OS to favor the correct GPU.

In Windows you must go to the 'Graphics settings' configuration page, add an
entry for ``python.exe`` for each of the conda environments *py36bench* and
*py39bench*, usually located at ``%USERPROFILE%\anaconda3\envs``. Then click on
the new ``python.exe`` entry in the list and select the correct GPU.

Desktop scaling
===============

For fair comparisons between Qt5 and Qt6 you must ensure that the desktop
scaling is set to 100%. This is because Qt5 does not scale the application
window according to the display scaling correctly, whereas Qt6 will.
