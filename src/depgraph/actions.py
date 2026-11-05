"""Действия инструмента, которые выбирает пользователь."""

import sys

from depgraph.config import TEST_MODE, format_config
from depgraph.errors import RepositoryError
from depgraph.graph import bfs, find_cycles
from depgraph.repository import FileRepository, MavenRepository


def create_repository(config):
    """Создать источник данных в соответствии с режимом работы."""
    if config.mode == TEST_MODE:
        return FileRepository(config.repository)
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


def collect_graph(repository, root):
    """Построить граф зависимостей пакета root.

    В граф попадают зависимости, нужные при выполнении пакета.
    Ошибка для корневого пакета прерывает работу, а для остальных
    выводится как предупреждение, и пакет остается без зависимостей.
    """
    def neighbors(package):
        """Вернуть имена зависимостей пакета."""
        try:
            items = repository.direct_dependencies(package)
        except RepositoryError as error:
            if package == root:
                raise
            print(f"warning: {package}: {error}", file=sys.stderr)
            return []
        return [item.name for item in items if item.transitive]

    return bfs([root], neighbors)


def format_edges(edges):
    """Сформировать строки ребер графа."""
    return [
        f"{node} -> {', '.join(children) or '(none)'}"
        for node, children in edges.items()
    ]


def format_cycles(edges):
    """Сформировать строки с найденными циклами."""
    cycles = find_cycles(edges)
    if not cycles:
        return ["cycles: none"]
    return ["cycles:"] + [" -> ".join(cycle) for cycle in cycles]


def show_graph(config):
    """Вывести граф зависимостей с учетом транзитивности."""
    repository = create_repository(config)
    traversal = collect_graph(repository, config.package)
    lines = [f"dependency graph of {config.package}:", "levels:"]
    lines.extend(
        f"{number}: {', '.join(level)}"
        for number, level in enumerate(traversal.levels)
    )
    lines.append("edges:")
    lines.extend(format_edges(traversal.edges))
    lines.extend(format_cycles(traversal.edges))
    lines.append(f"packages: {len(traversal.edges)}")
    return "\n".join(lines)


ACTIONS = {
    "config": show_config,
    "direct": show_direct,
    "graph": show_graph,
}
