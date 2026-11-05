"""Точка входа инструмента визуализации зависимостей."""

import sys

from depgraph.config import format_config, load_config
from depgraph.errors import ConfigError

CONFIG_ERROR_CODE = 2


def main(argv=None):
    """Запустить инструмент и вернуть код завершения."""
    try:
        config = load_config(argv)
    except ConfigError as error:
        print(f"error: {error}", file=sys.stderr)
        return CONFIG_ERROR_CODE
    print(format_config(config))
    return 0


if __name__ == "__main__":
    sys.exit(main())
