@echo off
rem Stage 5: Mermaid text and images of graphs for three packages.
pushd "%~dp0.."
set URL=https://repo1.maven.org/maven2

echo ===== 1. junit =====
python src\main.py --package junit:junit:4.13.2 --repo %URL% --action mermaid
echo exit code: %ERRORLEVEL%

echo ===== 2. guava =====
python src\main.py --package com.google.guava:guava:33.0.0-jre --repo %URL% --action mermaid
echo exit code: %ERRORLEVEL%

echo ===== 3. okhttp =====
python src\main.py --package com.squareup.okhttp3:okhttp:4.12.0 --repo %URL% --action mermaid
echo exit code: %ERRORLEVEL%

echo ===== 4. Test repository with cycles =====
python src\main.py --package A --repo repos\cycle.txt --mode test --action mermaid
echo exit code: %ERRORLEVEL%
popd
