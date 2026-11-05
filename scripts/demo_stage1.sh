#!/bin/sh
# Stage 1: all parameters and error handling for each of them.
cd "$(dirname "$0")/.." || exit 1
URL=https://repo1.maven.org/maven2

echo "===== 1. Valid parameters ====="
python3 src/main.py --package junit:junit:4.13.2 --repo "$URL" --action config
echo "exit code: $?"

echo "===== 2. Invalid package name ====="
python3 src/main.py --package junit --repo "$URL"
echo "exit code: $?"

echo "===== 3. Invalid repository URL ====="
python3 src/main.py --package junit:junit --repo ftp://example.com
echo "exit code: $?"

echo "===== 4. Invalid mode ====="
python3 src/main.py --package junit:junit --repo "$URL" --mode fast
echo "exit code: $?"

echo "===== 5. Missing test repository file ====="
python3 src/main.py --package A --repo nope.txt --mode test
echo "exit code: $?"

echo "===== 6. Directory instead of a test repository file ====="
python3 src/main.py --package A --repo scripts --mode test
echo "exit code: $?"

echo "===== 7. Invalid package name in the test mode ====="
python3 src/main.py --package abc --repo run.sh --mode test
echo "exit code: $?"

echo "===== 8. Missing required parameter ====="
python3 src/main.py --package junit:junit
echo "exit code: $?"
