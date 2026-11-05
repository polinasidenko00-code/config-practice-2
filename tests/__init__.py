"""Модульные тесты инструмента.

При импорте пакета tests каталог src добавляется в пути поиска
модулей, чтобы тесты могли импортировать пакет depgraph и модуль
main. Тесты запускаются из корня проекта:
python -m unittest discover -s tests -t .
"""

import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       os.pardir, "src")
sys.path.insert(0, os.path.normpath(SRC_DIR))
