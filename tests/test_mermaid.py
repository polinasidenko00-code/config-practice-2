"""Тесты визуализации графа."""

import os
import tempfile
import unittest
from unittest import mock

from depgraph.actions import show_mermaid
from depgraph.config import Config, load_config
from depgraph.mermaid import (
    MERMAID_SCRIPT,
    open_page,
    page_path,
    render_page,
    save_page,
    to_mermaid,
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


class TemporaryCwdTest(unittest.TestCase):
    """Базовый класс: запуск во временной текущей директории."""

    def enter_temporary_directory(self):
        """Перейти во временную директорию до конца теста."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(temp.name)


class ToMermaidTest(unittest.TestCase):
    """Проверка текста диаграммы."""

    def test_diagram(self):
        """Узлы получают номера, имена становятся подписями."""
        text = to_mermaid({"a:b:1": ["c:d:2"], "c:d:2": []})
        self.assertEqual(text.splitlines(), [
            "graph TD",
            '    n0["a:b:1"]',
            '    n1["c:d:2"]',
            "    n0 --> n1",
        ])

    def test_single_node(self):
        """Пакет без зависимостей выводится как один узел."""
        self.assertEqual(
            to_mermaid({"A": []}).splitlines(), ["graph TD", '    n0["A"]']
        )

    def test_cycle(self):
        """Цикл выводится обычными ребрами."""
        text = to_mermaid({"A": ["B"], "B": ["A"]})
        self.assertIn("n0 --> n1", text)
        self.assertIn("n1 --> n0", text)


class PageTest(TemporaryCwdTest):
    """Проверка страницы с изображением."""

    def test_render(self):
        """Диаграмма экранируется, подключается библиотека Mermaid."""
        page = render_page("a<b", "n0 --> n1")
        self.assertIn("a&lt;b", page)
        self.assertIn("n0 --&gt; n1", page)
        self.assertIn(MERMAID_SCRIPT, page)

    def test_path_is_safe(self):
        """Символы из имени пакета не попадают в путь."""
        self.assertEqual(
            page_path("a.b:c:1"), os.path.join("out", "graph_a.b_c_1.html")
        )

    def test_save(self):
        """Страница записывается в каталог out."""
        self.enter_temporary_directory()
        path = save_page("A", "graph TD")
        with open(path, encoding="utf-8") as file:
            self.assertIn("graph TD", file.read())

    def test_open(self):
        """Браузер получает адрес файла."""
        with mock.patch("webbrowser.open", return_value=True) as browser:
            self.assertTrue(open_page("graph.html"))
        self.assertTrue(browser.call_args[0][0].startswith("file:"))


class ShowMermaidTest(TemporaryCwdTest):
    """Проверка действия mermaid."""

    def run_action(self, open_browser):
        """Выполнить действие для примера repos/diamond.txt."""
        self.enter_temporary_directory()
        path = os.path.join(ROOT_DIR, "repos", "diamond.txt")
        config = Config("A", path, "test", "mermaid", open_browser)
        with mock.patch("webbrowser.open") as browser:
            return show_mermaid(config), browser

    def test_output(self):
        """Выводится текст диаграммы и путь к странице."""
        text, _browser = self.run_action(False)
        self.assertIn("graph TD", text)
        self.assertIn(os.path.join("out", "graph_A.html"), text)

    def test_browser_opened(self):
        """По умолчанию изображение открывается в браузере."""
        _text, browser = self.run_action(True)
        browser.assert_called_once()

    def test_no_browser(self):
        """С --no-browser браузер не открывается."""
        _text, browser = self.run_action(False)
        browser.assert_not_called()

    def test_option(self):
        """Параметр --no-browser попадает в настройки."""
        config = load_config(
            ["--package", "a:b", "--repo", "https://r.test", "--no-browser"]
        )
        self.assertFalse(config.open_browser)


if __name__ == "__main__":
    unittest.main()
