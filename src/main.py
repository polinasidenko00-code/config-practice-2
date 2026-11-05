"""Точка входа инструмента визуализации зависимостей."""

import sys

from depgraph.actions import ACTIONS
from depgraph.config import load_config
from depgraph.errors import ConfigError, RepositoryError

REPOSITORY_ERROR_CODE = 1
CONFIG_ERROR_CODE = 2


def main(argv=None):
    """Запустить инструмент и вернуть код завершения."""
    try:
        config = load_config(argv)
        print(ACTIONS[config.action](config))
    except ConfigError as error:
        print(f"error: {error}", file=sys.stderr)
        return CONFIG_ERROR_CODE
    except RepositoryError as error:
        print(f"error: {error}", file=sys.stderr)
        return REPOSITORY_ERROR_CODE
    return 0


if __name__ == "__main__":
    sys.exit(main())
