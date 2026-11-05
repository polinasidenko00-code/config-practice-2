"""Тесты построения графа и тестового репозитория."""

import contextlib
import io
import os
import tempfile
import unittest

from depgraph.actions import collect_graph, show_graph
from depgraph.config import Config
from depgraph.errors import RepositoryError
from depgraph.graph import bfs, find_cycles
from depgraph.repository import Dependency, FileRepository, parse_graph

ROOT_DIR = os.path.join(os.path.dirname(__file__), os.pardir)


def repo_file(name):
    """Вернуть путь к файлу из каталога repos."""
    return os.path.join(ROOT_DIR, "repos", name)


class BfsTest(unittest.TestCase):
    """Проверка обхода в ширину."""

    def test_levels(self):
        """Узлы разбиваются на уровни по расстоянию от корня."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        result = bfs(["A"], graph.get)
        self.assertEqual(result.levels, [["A"], ["B", "C"], ["D"]])
        self.assertEqual(result.edges, graph)

    def test_node_requested_once(self):
        """Соседи каждого узла запрашиваются один раз."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        calls = []

        def neighbors(node):
            """Запомнить запрос и вернуть соседей."""
            calls.append(node)
            return graph[node]

        bfs(["A"], neighbors)
        self.assertEqual(calls, ["A", "B", "C", "D"])

    def test_cycle_terminates(self):
        """Цикл не приводит к зацикливанию."""
        graph = {"A": ["B"], "B": ["A"]}
        self.assertEqual(bfs(["A"], graph.get).edges, graph)

    def test_self_loop(self):
        """Зависимость от самого себя обрабатывается."""
        result = bfs(["A"], {"A": ["A"]}.get)
        self.assertEqual(result.levels, [["A"]])

    def test_duplicates_removed(self):
        """Повторы в списке соседей убираются."""
        result = bfs(["A"], {"A": ["B", "B"], "B": []}.get)
        self.assertEqual(result.edges["A"], ["B"])


class FindCyclesTest(unittest.TestCase):
    """Проверка поиска циклов."""

    def test_no_cycles(self):
        """Ромб не является циклом."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        self.assertEqual(find_cycles(graph), [])

    def test_cycle(self):
        """Цикл выводится с повтором первого узла в конце."""
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        self.assertEqual(find_cycles(graph), [["A", "B", "C", "A"]])

    def test_self_loop(self):
        """Петля - цикл из одного узла."""
        self.assertEqual(find_cycles({"A": ["A"]}), [["A", "A"]])

    def test_several_cycles(self):
        """Находятся независимые циклы."""
        graph = {"A": ["B"], "B": ["A", "C"], "C": ["D"], "D": ["C"]}
        self.assertEqual(
            find_cycles(graph), [["A", "B", "A"], ["C", "D", "C"]]
        )


class ParseGraphTest(unittest.TestCase):
    """Проверка разбора файла тестового репозитория."""

    def test_graph(self):
        """Комментарии пропускаются, упомянутые пакеты добавляются."""
        text = "# comment\n\nA: B C\nB:\n"
        self.assertEqual(
            parse_graph(text), {"A": ["B", "C"], "B": [], "C": []}
        )

    def test_several_letters(self):
        """Имя может состоять из нескольких букв."""
        self.assertEqual(parse_graph("AB: CD"), {"AB": ["CD"], "CD": []})

    def test_invalid_lines(self):
        """Неверные строки сообщаются с номером."""
        for line in ("a: B", "A B", "A: b", "A: B1", ": B"):
            with self.assertRaisesRegex(RepositoryError, "line 2: invalid"):
                parse_graph(f"A:\n{line}")

    def test_defined_twice(self):
        """Повторное описание пакета - ошибка."""
        with self.assertRaisesRegex(RepositoryError, "defined twice"):
            parse_graph("A: B\nA: C")
        with self.assertRaisesRegex(RepositoryError, "defined twice"):
            parse_graph("A:\nA: C")

    def test_defined_after_mention(self):
        """Пакет можно описать после упоминания как зависимости."""
        self.assertEqual(parse_graph("A: B\nB: C")["B"], ["C"])


class FileRepositoryTest(unittest.TestCase):
    """Проверка тестового репозитория."""

    def test_dependencies(self):
        """Возвращаются прямые зависимости пакета."""
        repository = FileRepository(repo_file("diamond.txt"))
        self.assertEqual(
            repository.direct_dependencies("A"),
            [Dependency("B"), Dependency("C")],
        )

    def test_unknown_package(self):
        """Неизвестный пакет - ошибка."""
        repository = FileRepository(repo_file("simple.txt"))
        with self.assertRaisesRegex(RepositoryError, "Z not found"):
            repository.direct_dependencies("Z")

    def test_broken_file(self):
        """Файл с ошибкой сообщается с номером строки."""
        with self.assertRaisesRegex(RepositoryError, "line 3"):
            FileRepository(repo_file("broken.txt"))

    def test_binary_file(self):
        """Файл не в UTF-8 - ошибка чтения."""
        with tempfile.NamedTemporaryFile(delete=False) as file:
            file.write(b"\xff\xfe\xff")
        self.addCleanup(os.remove, file.name)
        with self.assertRaisesRegex(RepositoryError, "cannot read"):
            FileRepository(file.name)


class FakeRepository:
    """Репозиторий, в котором один пакет недоступен."""

    def direct_dependencies(self, package):
        """Вернуть зависимости или ошибку для пакета BAD."""
        if package == "BAD":
            raise RepositoryError("HTTP 404")
        return [
            Dependency("BAD"),
            Dependency("TESTONLY", "test"),
            Dependency("OPTIONAL", optional=True),
        ] if package == "A" else []


class CollectGraphTest(unittest.TestCase):
    """Проверка сбора графа из репозитория."""

    def test_only_runtime_dependencies(self):
        """test и optional зависимости не входят в граф."""
        with contextlib.redirect_stderr(io.StringIO()):
            result = collect_graph(FakeRepository(), "A")
        self.assertEqual(result.edges, {"A": ["BAD"], "BAD": []})

    def test_warning_for_transitive_error(self):
        """Ошибка для зависимости выводится как предупреждение."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            collect_graph(FakeRepository(), "A")
        self.assertIn("warning: BAD: HTTP 404", err.getvalue())

    def test_error_for_root(self):
        """Ошибка для корневого пакета прерывает работу."""
        with self.assertRaises(RepositoryError):
            collect_graph(FakeRepository(), "BAD")


class ShowGraphTest(unittest.TestCase):
    """Проверка вывода графа для примеров репозиториев."""

    def show(self, name, package="A"):
        """Вывести граф пакета из файла repos."""
        return show_graph(
            Config(package, repo_file(name), "test", "graph")
        ).splitlines()

    def test_diamond(self):
        """Ромб: уровни, ребра, отсутствие циклов."""
        self.assertEqual(self.show("diamond.txt"), [
            "dependency graph of A:",
            "levels:",
            "0: A",
            "1: B, C",
            "2: D",
            "3: E",
            "edges:",
            "A -> B, C",
            "B -> D",
            "C -> D",
            "D -> E",
            "E -> (none)",
            "cycles: none",
            "packages: 5",
        ])

    def test_cycles(self):
        """Циклы перечисляются в выводе."""
        lines = self.show("cycle.txt")
        self.assertIn("A -> B -> C -> A", lines)
        self.assertIn("D -> E -> D", lines)

    def test_part_of_forest(self):
        """В граф входит только достижимая часть репозитория."""
        lines = self.show("forest.txt", "TOOL")
        self.assertIn("packages: 5", lines)
        self.assertNotIn("APP -> LIB, CORE", lines)


if __name__ == "__main__":
    unittest.main()
