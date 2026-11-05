@echo off
rem Stage 3: dependency graph, cycles and the test repository mode.
pushd "%~dp0.."

echo ===== 1. Chain =====
python src\main.py --package A --repo repos\simple.txt --mode test
echo exit code: %ERRORLEVEL%

echo ===== 2. Diamond: a shared package is visited once =====
python src\main.py --package A --repo repos\diamond.txt --mode test
echo exit code: %ERRORLEVEL%

echo ===== 3. Cyclic dependencies =====
python src\main.py --package A --repo repos\cycle.txt --mode test
echo exit code: %ERRORLEVEL%

echo ===== 4. Package depends on itself =====
python src\main.py --package A --repo repos\self_loop.txt --mode test
echo exit code: %ERRORLEVEL%

echo ===== 5. Only a reachable part of the repository =====
python src\main.py --package TOOL --repo repos\forest.txt --mode test
echo exit code: %ERRORLEVEL%

echo ===== 6. Package without dependencies =====
python src\main.py --package SOLO --repo repos\forest.txt --mode test
echo exit code: %ERRORLEVEL%

echo ===== 7. Unknown package =====
python src\main.py --package Z --repo repos\simple.txt --mode test
echo exit code: %ERRORLEVEL%

echo ===== 8. Broken repository file =====
python src\main.py --package A --repo repos\broken.txt --mode test
echo exit code: %ERRORLEVEL%

echo ===== 9. Real repository =====
python src\main.py --package com.squareup.okhttp3:okhttp:4.12.0 --repo https://repo1.maven.org/maven2
echo exit code: %ERRORLEVEL%
popd
