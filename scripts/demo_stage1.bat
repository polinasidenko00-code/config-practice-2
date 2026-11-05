@echo off
rem Stage 1: all parameters and error handling for each of them.
pushd "%~dp0.."
set URL=https://repo1.maven.org/maven2

echo ===== 1. Valid parameters =====
python src\main.py --package junit:junit:4.13.2 --repo %URL%
echo exit code: %ERRORLEVEL%

echo ===== 2. Invalid package name =====
python src\main.py --package junit --repo %URL%
echo exit code: %ERRORLEVEL%

echo ===== 3. Invalid repository URL =====
python src\main.py --package junit:junit --repo ftp://example.com
echo exit code: %ERRORLEVEL%

echo ===== 4. Invalid mode =====
python src\main.py --package junit:junit --repo %URL% --mode fast
echo exit code: %ERRORLEVEL%

echo ===== 5. Missing test repository file =====
python src\main.py --package A --repo nope.txt --mode test
echo exit code: %ERRORLEVEL%

echo ===== 6. Directory instead of a test repository file =====
python src\main.py --package A --repo scripts --mode test
echo exit code: %ERRORLEVEL%

echo ===== 7. Invalid package name in the test mode =====
python src\main.py --package abc --repo run.bat --mode test
echo exit code: %ERRORLEVEL%

echo ===== 8. Missing required parameter =====
python src\main.py --package junit:junit
echo exit code: %ERRORLEVEL%
popd
