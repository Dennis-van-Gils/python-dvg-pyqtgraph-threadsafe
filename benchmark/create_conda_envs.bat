@echo off
set NAME_ENV_PY36=py36bench
set NAME_ENV_PY310=py310bench

REM Python 3.6
call conda create -c conda-forge -n %NAME_ENV_PY36% python=3.6
call conda activate %NAME_ENV_PY36%
pip install pyqt5 pyside2
pip install -r requirements.txt

REM Python 3.10
call conda create -c conda-forge -n %NAME_ENV_PY310% python=3.10
call conda activate %NAME_ENV_PY310%
pip install pyqt5 pyqt6 pyside2 pyside6
pip install -r requirements.txt

GOTO End


REM --------------------
REM Alternative channels
REM Might help when any of the Qt libraries fail to install with the method above
REM Might result in lower Qt minor-versions to get installed
REM --------------------

REM Python 3.6
call conda create -c conda-forge -n %NAME_ENV_PY36% python=3.6 numpy pyopengl pyqt pyside2
call conda activate %NAME_ENV_PY36%
pip install -r requirements.txt

REM Python 3.10
call conda create -c conda-forge -n %NAME_ENV_PY310% python=3.10 numpy pyopengl pyqt pyside2
call conda activate %NAME_ENV_PY310%
pip install pyqt6 pyside6
pip install -r requirements.txt


:End
echo:
echo:
echo Created conda environments `%NAME_ENV_PY36%` and `%NAME_ENV_PY310%`
echo Ready to run the benchmark by calling:
echo ^> automate_benchmarks.bat
echo or
echo ^> python benchmark.py pyside2