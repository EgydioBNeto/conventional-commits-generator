@echo off
REM Script to set up a virtual environment for CCG development on Windows

REM Set the virtual environment name
SET VENV_NAME=.venv

echo Setting up a virtual environment for CCG development...

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python first.
    exit /b 1
)

REM Create the virtual environment
echo Creating virtual environment...
python -m venv %VENV_NAME%

REM Activate the virtual environment
echo Activating virtual environment...
call %VENV_NAME%\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install the package in development mode with dev dependencies
echo Installing CCG in development mode...
pip install -e .[dev]

REM Install pre-commit hooks
echo Setting up pre-commit hooks...
pre-commit install

echo.
echo Setup complete! Virtual environment is ready.
echo.
echo To activate the virtual environment:
echo   call %VENV_NAME%\Scripts\activate.bat
echo To deactivate:
echo   deactivate
