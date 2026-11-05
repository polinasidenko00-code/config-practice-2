#!/bin/sh
# Запуск программы: ./run.sh --package NAME --repo URL_OR_PATH [опции]
# Запуск тестов:    ./run.sh test
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "$1" = "test" ]; then
    cd "$DIR" && python3 -m unittest discover -s tests -t . -v
else
    python3 "$DIR/src/main.py" "$@"
fi
