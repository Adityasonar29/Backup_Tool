@echo off
cd /d "%~dp0"

REM Create virtual environment if not exists
if not exist .venv (
    python -m venv .venv
)

REM Activate and install requirements
call .venv\Scripts\activate.bat
pip install -r requirements.txt

REM Copy .env.example to .env if needed
if exist .env.example (
    if not exist .env (
        copy .env.example .env
    )
)

echo Setup complete!
echo To activate the environment later, run:
echo     .venv\Scripts\activate
pause