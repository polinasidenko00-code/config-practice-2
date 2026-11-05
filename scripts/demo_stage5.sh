#!/bin/sh
# Stage 5: Mermaid text and images of graphs for three packages.
cd "$(dirname "$0")/.." || exit 1
URL=https://repo1.maven.org/maven2

echo "===== 1. junit ====="
python3 src/main.py --package junit:junit:4.13.2 --repo "$URL" --action mermaid
echo "exit code: $?"

echo "===== 2. guava ====="
python3 src/main.py --package com.google.guava:guava:33.0.0-jre --repo "$URL" --action mermaid
echo "exit code: $?"

echo "===== 3. okhttp ====="
python3 src/main.py --package com.squareup.okhttp3:okhttp:4.12.0 --repo "$URL" --action mermaid
echo "exit code: $?"

echo "===== 4. Test repository with cycles ====="
python3 src/main.py --package A --repo repos/cycle.txt --mode test --action mermaid
echo "exit code: $?"
