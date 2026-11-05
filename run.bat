@echo off
rem Run the tool: run.bat --package NAME --repo URL_OR_PATH [options]
rem Run tests:    run.bat test
if "%1"=="test" (
    pushd "%~dp0"
    python -m unittest discover -s tests -t . -v
    popd
) else (
    python "%~dp0src\main.py" %*
)
