"""Тесты обратных зависимостей."""

import os
import unittest

from depgraph.actions import show_reverse
from depgraph.config import Config, load_config
from depgraph.errors import RepositoryError
from depgraph.graph import reverse_edges

ROOT_DIR = os.path.join(os.path.dirname(__file__), os.pardir)
URL = "https://repo1.maven.org/maven2"


def show(name, package):
    """Вывести обратные зависимости пакета из файла repos."""
    path = os.path.join(ROOT_DIR, "repos", name)
    config = Config(package, path, "test", "reverse")
    return show_reverse(config).splitlines()


class ReverseEdgesTest(unittest.TestCase):
    """Проверка разворота ребер."""

    def test_reverse(self):
        """Каждое ребро меняет направление."""
        self.assertEqual(
            reverse_edges({"A": ["B", "C"], "B": ["C"], "C": []}),
            {"A": [], "B": ["A"], "C": ["A", "B"]},
        )


class ShowReverseTest(unittest.TestCase):
    """Проверка вывода обратных зависимостей."""

    def test_diamond(self):
        """Выводятся прямые и транзитивные зависимые пакеты."""
        self.assertEqual(show("diamond.txt", "E"), [
            "reverse dependencies of E:",
            "levels:",
            "0: E",
            "1: D",
            "2: B, C",
            "3: A",
            "edges (package <- dependents):",
            "E <- D",
            "D <- B, C",
            "B <- A",
            "C <- A",
            "A <- (none)",
            "dependents: 4",
        ])

    def test_no_dependents(self):
        """От корневого пакета никто не зависит."""
        self.assertEqual(
            show("diamond.txt", "A"), ["no packages depend on A"]
        )

    def test_cycle_terminates(self):
        """Циклы не мешают обходу."""
        lines = show("cycle.txt", "A")
        self.assertIn("1: C", lines)
        self.assertIn("2: B", lines)
        self.assertIn("dependents: 2", lines)

    def test_self_loop(self):
        """Пакет не считается зависимым от самого себя."""
        self.assertEqual(
            show("self_loop.txt", "A"), ["no packages depend on A"]
        )

    def test_several_roots(self):
        """Учитываются пакеты из разных частей репозитория."""
        lines = show("forest.txt", "UTIL")
        self.assertIn("1: LIB, CORE", lines)
        self.assertIn("2: APP, PLUGIN", lines)
        self.assertIn("3: TOOL", lines)

    def test_unknown_package(self):
        """Неизвестный пакет - ошибка."""
        with self.assertRaisesRegex(RepositoryError, "Z not found"):
            show("simple.txt", "Z")

    def test_real_mode(self):
        """В реальном режиме обратные зависимости недоступны."""
        config = load_config(
            ["--package", "a:b", "--repo", URL, "--action", "reverse"]
        )
        with self.assertRaisesRegex(RepositoryError, "need the test mode"):
            show_reverse(config)


if __name__ == "__main__":
    unittest.main()
