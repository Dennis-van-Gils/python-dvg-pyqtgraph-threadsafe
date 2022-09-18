@echo off
set NAME_ENV_PY36=py36bench
set NAME_ENV_PY39=py39bench

REM Python 3.6
call conda create -c conda-forge -n %NAME_ENV_PY36% python=3.6
call conda activate %NAME_ENV_PY36%
pip install ipython black pylint
pip install pyqt5 pyside2
pip install -r requirements.txt

REM Python 3.9
call conda create -c conda-forge -n %NAME_ENV_PY39% python=3.9
call conda activate %NAME_ENV_PY39%
pip install ipython black pylint
pip install pyqt5 pyqt6 pyside2 pyside6
pip install -r requirements.txt

GOTO End


REM --------------------
REM Alternative channels
REM --------------------

REM Python 3.6
call conda create -c conda-forge -n %NAME_ENV_PY36% python=3.6 ipython black pylint numpy pyopengl pyqt pyside2
call conda activate %NAME_ENV_PY36%
pip install -r requirements.txt

REM Python 3.9
call conda create -c conda-forge -n %NAME_ENV_PY39% python=3.9 ipython black pylint numpy pyopengl pyqt pyside2
call conda activate %NAME_ENV_PY39%
pip install pyqt6 pyside6
pip install -r requirements.txt


:End
echo:
echo:
echo Created conda environments `%NAME_ENV_PY36%` and `%NAME_ENV_PY39%`
echo Ready to run the benchmark by calling:
echo ^> automate_benchmarks.bat
echo or
echo ^> python benchmark.py pyside2