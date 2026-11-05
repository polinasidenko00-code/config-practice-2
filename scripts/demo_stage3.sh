#!/bin/sh
# Stage 3: dependency graph, cycles and the test repository mode.
cd "$(dirname "$0")/.." || exit 1

echo "===== 1. Chain ====="
python3 src/main.py --package A --repo repos/simple.txt --mode test
echo "exit code: $?"

echo "===== 2. Diamond: a shared package is visited once ====="
python3 src/main.py --package A --repo repos/diamond.txt --mode test
echo "exit code: $?"

echo "===== 3. Cyclic dependencies ====="
python3 src/main.py --package A --repo repos/cycle.txt --mode test
echo "exit code: $?"

echo "===== 4. Package depends on itself ====="
python3 src/main.py --package A --repo repos/self_loop.txt --mode test
echo "exit code: $?"

echo "===== 5. Only a reachable part of the repository ====="
python3 src/main.py --package TOOL --repo repos/forest.txt --mode test
echo "exit code: $?"

echo "===== 6. Package without dependencies ====="
python3 src/main.py --package SOLO --repo repos/forest.txt --mode test
echo "exit code: $?"

echo "===== 7. Unknown package ====="
python3 src/main.py --package Z --repo repos/simple.txt --mode test
echo "exit code: $?"

echo "===== 8. Broken repository file ====="
python3 src/main.py --package A --repo repos/broken.txt --mode test
echo "exit code: $?"

echo "===== 9. Real repository ====="
python3 src/main.py --package com.squareup.okhttp3:okhttp:4.12.0 --repo https://repo1.maven.org/maven2
echo "exit code: $?"
