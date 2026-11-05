#!/bin/sh
# Stage 4: reverse dependencies in the test repository.
cd "$(dirname "$0")/.." || exit 1

echo "===== 1. Chain: who depends on D ====="
python3 src/main.py --package D --repo repos/simple.txt --mode test --action reverse
echo "exit code: $?"

echo "===== 2. Diamond: who depends on E ====="
python3 src/main.py --package E --repo repos/diamond.txt --mode test --action reverse
echo "exit code: $?"

echo "===== 3. Cycle: who depends on A ====="
python3 src/main.py --package A --repo repos/cycle.txt --mode test --action reverse
echo "exit code: $?"

echo "===== 4. Several parts of a repository: who depends on UTIL ====="
python3 src/main.py --package UTIL --repo repos/forest.txt --mode test --action reverse
echo "exit code: $?"

echo "===== 5. Nobody depends on the package ====="
python3 src/main.py --package APP --repo repos/forest.txt --mode test --action reverse
echo "exit code: $?"

echo "===== 6. Unknown package ====="
python3 src/main.py --package Z --repo repos/simple.txt --mode test --action reverse
echo "exit code: $?"

echo "===== 7. Real repository is not supported ====="
python3 src/main.py --package junit:junit --repo https://repo1.maven.org/maven2 --action reverse
echo "exit code: $?"
