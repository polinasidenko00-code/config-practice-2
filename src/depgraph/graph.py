"""Построение графа зависимостей и поиск циклов."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Traversal:
    """Результат обхода: ребра графа и уровни обхода в ширину."""

    edges: Dict[str, List[str]] = field(default_factory=dict)
    levels: List[List[str]] = field(default_factory=list)


def bfs(frontier, neighbors, traversal=None):
    """Обойти граф в ширину с помощью рекурсии.

    Один вызов обрабатывает один уровень: для всех узлов frontier
    запрашивает соседей функцией neighbors и рекурсивно переходит
    к следующему уровню. В него попадают только еще не посещенные
    узлы, поэтому циклические зависимости не приводят к зацикливанию.
    """
    if traversal is None:
        traversal = Traversal()
    traversal.levels.append(list(frontier))
    for node in frontier:
        traversal.edges[node] = list(dict.fromkeys(neighbors(node)))
    next_level = dict.fromkeys(
        child for node in frontier for child in traversal.edges[node]
        if child not in traversal.edges
    )
    if next_level:
        bfs(list(next_level), neighbors, traversal)
    return traversal


def reverse_edges(edges):
    """Построить граф, в котором все ребра направлены обратно."""
    reversed_edges = {node: [] for node in edges}
    for node, children in edges.items():
        for child in children:
            reversed_edges[child].append(node)
    return reversed_edges


def find_cycles(edges):
    """Найти циклы в графе поиском в глубину.

    Возвращает список циклов; цикл - список узлов, в котором
    первый и последний узлы совпадают.
    """
    cycles = []
    finished = set()
    for node in edges:
        visit(node, edges, [], finished, cycles)
    return cycles


def visit(node, edges, path, finished, cycles):
    """Посетить узел; повтор узла в текущем пути означает цикл."""
    if node in path:
        cycles.append(path[path.index(node):] + [node])
        return
    if node in finished:
        return
    path.append(node)
    for child in edges.get(node, []):
        visit(child, edges, path, finished, cycles)
    path.pop()
    finished.add(node)
