@echo off
rem Stage 2: direct dependencies from a real Maven repository.
pushd "%~dp0.."
set URL=https://repo1.maven.org/maven2

echo ===== 1. Package with a fixed version =====
python src\main.py --package junit:junit:4.13.2 --repo %URL% --action direct
echo exit code: %ERRORLEVEL%

echo ===== 2. Latest version of a package =====
python src\main.py --package junit:junit --repo %URL% --action direct
echo exit code: %ERRORLEVEL%

echo ===== 3. Versions from a parent POM and an imported BOM =====
python src\main.py --package org.springframework.boot:spring-boot-starter-web:3.2.0 --repo %URL% --action direct
echo exit code: %ERRORLEVEL%

echo ===== 4. Test and optional dependencies are shown too =====
python src\main.py --package org.apache.commons:commons-text:1.11.0 --repo %URL% --action direct
echo exit code: %ERRORLEVEL%

echo ===== 5. Package does not exist =====
python src\main.py --package no.such:package:1 --repo %URL% --action direct
echo exit code: %ERRORLEVEL%
popd
