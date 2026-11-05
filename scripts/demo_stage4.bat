@echo off
rem Stage 4: reverse dependencies in the test repository.
pushd "%~dp0.."

echo ===== 1. Chain: who depends on D =====
python src\main.py --package D --repo repos\simple.txt --mode test --action reverse
echo exit code: %ERRORLEVEL%

echo ===== 2. Diamond: who depends on E =====
python src\main.py --package E --repo repos\diamond.txt --mode test --action reverse
echo exit code: %ERRORLEVEL%

echo ===== 3. Cycle: who depends on A =====
python src\main.py --package A --repo repos\cycle.txt --mode test --action reverse
echo exit code: %ERRORLEVEL%

echo ===== 4. Several parts of a repository: who depends on UTIL =====
python src\main.py --package UTIL --repo repos\forest.txt --mode test --action reverse
echo exit code: %ERRORLEVEL%

echo ===== 5. Nobody depends on the package =====
python src\main.py --package APP --repo repos\forest.txt --mode test --action reverse
echo exit code: %ERRORLEVEL%

echo ===== 6. Unknown package =====
python src\main.py --package Z --repo repos\simple.txt --mode test --action reverse
echo exit code: %ERRORLEVEL%

echo ===== 7. Real repository is not supported =====
python src\main.py --package junit:junit --repo https://repo1.maven.org/maven2 --action reverse
echo exit code: %ERRORLEVEL%
popd
