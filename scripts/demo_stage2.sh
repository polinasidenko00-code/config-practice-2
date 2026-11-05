#!/bin/sh
# Stage 2: direct dependencies from a real Maven repository.
cd "$(dirname "$0")/.." || exit 1
URL=https://repo1.maven.org/maven2

echo "===== 1. Package with a fixed version ====="
python3 src/main.py --package junit:junit:4.13.2 --repo "$URL" --action direct
echo "exit code: $?"

echo "===== 2. Latest version of a package ====="
python3 src/main.py --package junit:junit --repo "$URL" --action direct
echo "exit code: $?"

echo "===== 3. Versions from a parent POM and an imported BOM ====="
python3 src/main.py --package org.springframework.boot:spring-boot-starter-web:3.2.0 --repo "$URL" --action direct
echo "exit code: $?"

echo "===== 4. Test and optional dependencies are shown too ====="
python3 src/main.py --package org.apache.commons:commons-text:1.11.0 --repo "$URL" --action direct
echo "exit code: $?"

echo "===== 5. Package does not exist ====="
python3 src/main.py --package no.such:package:1 --repo "$URL" --action direct
echo "exit code: $?"
