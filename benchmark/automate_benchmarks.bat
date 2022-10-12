@echo off
goto bench310

REM Python 3.6
:bench36

call conda activate py36bench

pip install pyqtgraph==0.11.0
python benchmark.py pyqt5
python benchmark.py pyside2

pip install pyqtgraph==0.11.1
python benchmark.py pyqt5
python benchmark.py pyside2

REM Python 3.10
:bench310

call conda activate py310bench

pip install pyqtgraph==0.11.0
python benchmark.py pyqt5
python benchmark.py pyside2

pip install pyqtgraph==0.11.1
python benchmark.py pyqt5
python benchmark.py pyside2

pip install pyqtgraph==0.12.4
python benchmark.py pyqt5
python benchmark.py pyqt6
python benchmark.py pyside2
python benchmark.py pyside6

pip install -U pyqtgraph
python benchmark.py pyqt5
python benchmark.py pyqt6
python benchmark.py pyside2
python benchmark.py pyside6

REM Ensure we restore the terminal color
echo [0m