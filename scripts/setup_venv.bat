@echo off
REM Script to set up a virtual environment for CCG development on Windows

REM Set the virtual environment name
SET VENV_NAME=.venv

REM Check for reinstall flag
SET REINSTALL=0
IF "%1"=="--reinstall" SET REINSTALL=1
IF "%1"=="-r" SET REINSTALL=1

REM Check if venv exists
IF EXIST %VENV_NAME% (
    echo Virtual environment already exists.

    IF %REINSTALL%==1 (
        echo Reinstalling CCG within existing virtual environment...

        REM Activate the virtual environment
        call %VENV_NAME%\Scripts\activate.bat

        REM Reinstall the package in development mode
        echo Reinstalling CCG in development mode...
        pip uninstall -y ccg
        pip install -e .[dev]

        echo CCG has been reinstalled successfully.
        goto :end
    ) ELSE (
        echo Use '--reinstall' or '-r' flag to reinstall CCG without recreating the venv.
        echo Example: %0 --reinstall

        REM Ask if user wants to continue with full setup
        set /p CONTINUE="Do you want to continue with full setup? (y/n): "
        if /i "%CONTINUE%"=="n" goto :end
    )
)

echo Setting up a virtual environment for CCG development...

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python first.
    exit /b 1
)

REM Create the virtual environment if it doesn't exist
IF NOT EXIST %VENV_NAME% (
    echo Creating virtual environment...
    python -m venv %VENV_NAME%
) ELSE (
    echo Using existing virtual environment.
)

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

:end
echo.
echo Setup complete! Virtual environment is ready.
echo.
echo To activate the virtual environment:
echo   call %VENV_NAME%\Scripts\activate.bat
echo To reinstall after changes:
echo   %0 --reinstall
echo To deactivate:
echo   deactivate

REM Keep the environment active
