"""Действия инструмента, которые выбирает пользователь."""

from depgraph.config import TEST_MODE, format_config
from depgraph.errors import RepositoryError
from depgraph.repository import MavenRepository


def create_repository(config):
    """Создать источник данных в соответствии с режимом работы."""
    if config.mode == TEST_MODE:
        raise RepositoryError("the test mode is not supported yet")
    return MavenRepository(config.repository)


def format_dependency(dependency):
    """Сформировать строку с именем и свойствами зависимости."""
    details = dependency.scope
    if dependency.optional:
        details = f"{details}, optional"
    return f"{dependency.name} ({details})"


def show_config(config):
    """Вывести параметры запуска в формате ключ-значение."""
    return format_config(config)


def show_direct(config):
    """Вывести все прямые зависимости пакета."""
    repository = create_repository(config)
    dependencies = repository.direct_dependencies(config.package)
    if not dependencies:
        return f"{config.package} has no direct dependencies"
    lines = [f"direct dependencies of {config.package}:"]
    lines.extend(format_dependency(item) for item in dependencies)
    return "\n".join(lines)


ACTIONS = {
    "config": show_config,
    "direct": show_direct,
}
