"""Исключения инструмента."""


class ConfigError(Exception):
    """Ошибка в параметрах, заданных пользователем."""


class RepositoryError(Exception):
    """Ошибка получения данных из репозитория."""
