@echo off
REM This script is used to run the backup CLI tool
REM Activate the virtual environment
call "E:\Adi_32GR_files\MyCodingHelper\Projects\python_projects\.venv_laptop\Scripts\activate.bat"

REM Set UTF-8 output for Python
set PYTHONIOENCODING=utf-8


REM Change code page to UTF-8
chcp 65001

REM Run your Python script, passing all arguments
python "D:\its_adi\files\backup_tool\backup_cli.py" %*