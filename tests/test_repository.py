"""Тесты разбора POM и получения прямых зависимостей."""

import contextlib
import io
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError

from depgraph.config import Config
from depgraph.actions import show_direct
from depgraph.errors import RepositoryError
from depgraph.pom import interpolate, parse_latest_version, parse_pom
from depgraph.repository import (
    Dependency,
    MavenRepository,
    clean_version,
    fetch_url,
    split_package,
)
from main import main

URL = "https://repo.test/maven2"
NAMESPACE = 'xmlns="http://maven.apache.org/POM/4.0.0"'


def dep(group, artifact, version="", extra=""):
    """Сформировать элемент dependency для тестового POM."""
    version_tag = f"<version>{version}</version>" if version else ""
    return (
        f"<dependency><groupId>{group}</groupId>"
        f"<artifactId>{artifact}</artifactId>{version_tag}{extra}"
        "</dependency>"
    )


def pom(body):
    """Сформировать тестовый POM в байтах."""
    return f"<project {NAMESPACE}>{body}</project>".encode("utf-8")


def pom_url(group, artifact, version):
    """Построить адрес POM в тестовом репозитории."""
    path = group.replace(".", "/")
    return f"{URL}/{path}/{artifact}/{version}/{artifact}-{version}.pom"


def make_fetch(files):
    """Создать функцию скачивания из словаря адрес -> байты."""
    def fetch(url):
        """Вернуть файл или ошибку 404."""
        if url not in files:
            raise RepositoryError(f"cannot download {url}: HTTP 404")
        return files[url]
    return fetch


def names(repository, package):
    """Вернуть имена прямых зависимостей пакета."""
    return [
        item.name for item in repository.direct_dependencies(package)
    ]


class PomTest(unittest.TestCase):
    """Проверка разбора POM-файла."""

    def test_fields(self):
        """Разбираются координаты, родитель, свойства, зависимости."""
        parsed = parse_pom(pom(
            "<parent><groupId>p</groupId><artifactId>q</artifactId>"
            "<version>1</version></parent>"
            "<artifactId>a</artifactId>"
            "<properties><x.y>2</x.y></properties>"
            f"<dependencies>{dep('g', 'b', '3')}</dependencies>"
        ))
        self.assertEqual(parsed.parent, ("p", "q", "1"))
        self.assertEqual(parsed.artifact, "a")
        self.assertEqual(parsed.properties, {"x.y": "2"})
        self.assertEqual(parsed.dependencies[0].version, "3")

    def test_managed_not_mixed_with_dependencies(self):
        """dependencyManagement не считается зависимостями."""
        parsed = parse_pom(pom(
            "<dependencyManagement><dependencies>"
            f"{dep('g', 'b', '3')}"
            "</dependencies></dependencyManagement>"
        ))
        self.assertEqual(parsed.dependencies, [])
        self.assertEqual(parsed.managed[0].artifact, "b")

    def test_invalid_xml(self):
        """Некорректный XML - ошибка репозитория."""
        with self.assertRaisesRegex(RepositoryError, "invalid XML"):
            parse_pom(b"<project>")

    def test_not_a_pom(self):
        """Другой корневой элемент - ошибка репозитория."""
        with self.assertRaisesRegex(RepositoryError, "not a POM"):
            parse_pom(b"<html></html>")

    def test_interpolate(self):
        """Свойства подставляются, в том числе вложенные."""
        properties = {"a": "${b}", "b": "1"}
        self.assertEqual(interpolate("v${a}", properties), "v1")
        self.assertEqual(interpolate("${c}", properties), "${c}")
        self.assertIsNone(interpolate(None, properties))

    def test_interpolate_cycle(self):
        """Циклические свойства не приводят к зависанию."""
        self.assertEqual(interpolate("${a}", {"a": "${a}"}), "${a}")

    def test_latest_version(self):
        """Версия берется из release, latest или списка versions."""
        cases = {
            "<release>2</release><latest>3</latest>": "2",
            "<latest>3</latest>": "3",
            "<versions><version>1</version><version>4</version>"
            "</versions>": "4",
        }
        for body, expected in cases.items():
            data = f"<metadata><versioning>{body}</versioning></metadata>"
            self.assertEqual(
                parse_latest_version(data.encode("utf-8")), expected
            )

    def test_no_versions(self):
        """Метаданные без версий - ошибка."""
        with self.assertRaisesRegex(RepositoryError, "no versions"):
            parse_latest_version(b"<metadata></metadata>")


class HelpersTest(unittest.TestCase):
    """Проверка вспомогательных функций."""

    def test_split_package(self):
        """Имя делится на группу, артефакт и версию."""
        self.assertEqual(split_package("g:a"), ("g", "a", None))
        self.assertEqual(split_package("g:a:1"), ("g", "a", "1"))

    def test_clean_version(self):
        """Диапазоны и неразрешенные свойства не считаются версией."""
        self.assertEqual(clean_version("1.0"), "1.0")
        for version in (None, "", "${x}", "[1,2)", "(,2]"):
            self.assertIsNone(clean_version(version))

    def test_transitive(self):
        """В граф попадают только compile и runtime без optional."""
        self.assertTrue(Dependency("a").transitive)
        self.assertTrue(Dependency("a", "runtime").transitive)
        self.assertFalse(Dependency("a", "test").transitive)
        self.assertFalse(Dependency("a", "provided").transitive)
        self.assertFalse(Dependency("a", optional=True).transitive)


class MavenRepositoryTest(unittest.TestCase):
    """Проверка получения прямых зависимостей."""

    def test_direct_dependencies(self):
        """Зависимости получают область и признак optional."""
        files = {pom_url("org.g", "a", "1"): pom(
            "<dependencies>"
            + dep("x", "b", "2")
            + dep("x", "c", "3", "<scope>test</scope>")
            + dep("x", "d", "4", "<optional>true</optional>")
            + "</dependencies>"
        )}
        items = MavenRepository(
            URL, make_fetch(files)
        ).direct_dependencies("org.g:a:1")
        self.assertEqual(items, [
            Dependency("x:b:2"),
            Dependency("x:c:3", "test"),
            Dependency("x:d:4", optional=True),
        ])

    def test_trailing_slash_in_url(self):
        """Завершающий слэш в адресе не мешает."""
        files = {pom_url("g", "a", "1"): pom("")}
        repository = MavenRepository(URL + "/", make_fetch(files))
        self.assertEqual(names(repository, "g:a:1"), [])

    def test_latest_version_used(self):
        """Без версии используется последняя из метаданных."""
        files = {
            f"{URL}/g/a/maven-metadata.xml":
                b"<metadata><versioning><release>7</release>"
                b"</versioning></metadata>",
            pom_url("g", "a", "7"): pom(
                f"<dependencies>{dep('x', 'b', '2')}</dependencies>"
            ),
        }
        repository = MavenRepository(URL, make_fetch(files))
        self.assertEqual(names(repository, "g:a"), ["x:b:2"])

    def test_properties(self):
        """Версии из свойств и project.version подставляются."""
        files = {pom_url("g", "a", "1"): pom(
            "<version>1</version><groupId>g</groupId>"
            "<properties><b.version>5</b.version></properties>"
            "<dependencies>"
            + dep("x", "b", "${b.version}")
            + dep("${project.groupId}", "c", "${project.version}")
            + "</dependencies>"
        )}
        repository = MavenRepository(URL, make_fetch(files))
        self.assertEqual(names(repository, "g:a:1"), ["x:b:5", "g:c:1"])

    def test_parent(self):
        """От родителя наследуются свойства, версии и зависимости."""
        files = {
            pom_url("p", "parent", "9"): pom(
                "<properties><v>2</v></properties>"
                "<dependencyManagement><dependencies>"
                f"{dep('x', 'managed', '${v}', '<scope>runtime</scope>')}"
                "</dependencies></dependencyManagement>"
                f"<dependencies>{dep('x', 'inherited', '1')}</dependencies>"
            ),
            pom_url("g", "a", "1"): pom(
                "<parent><groupId>p</groupId>"
                "<artifactId>parent</artifactId><version>9</version>"
                "</parent>"
                f"<dependencies>{dep('x', 'managed')}</dependencies>"
            ),
        }
        items = MavenRepository(
            URL, make_fetch(files)
        ).direct_dependencies("g:a:1")
        self.assertEqual(items, [
            Dependency("x:inherited:1"),
            Dependency("x:managed:2", "runtime"),
        ])

    def test_bom_import(self):
        """Версии импортируются из BOM; своя запись важнее."""
        files = {
            pom_url("b", "bom", "1"): pom(
                "<dependencyManagement><dependencies>"
                + dep("x", "one", "10") + dep("x", "two", "20")
                + "</dependencies></dependencyManagement>"
            ),
            pom_url("g", "a", "1"): pom(
                "<dependencyManagement><dependencies>"
                + dep("x", "two", "21")
                + dep("b", "bom", "1", "<scope>import</scope>")
                + "</dependencies></dependencyManagement><dependencies>"
                + dep("x", "one") + dep("x", "two")
                + "</dependencies>"
            ),
        }
        repository = MavenRepository(URL, make_fetch(files))
        self.assertEqual(names(repository, "g:a:1"), ["x:one:10", "x:two:21"])

    def test_unknown_version(self):
        """Диапазон и неизвестная версия дают имя без версии."""
        files = {pom_url("g", "a", "1"): pom(
            "<dependencies>"
            + dep("x", "b", "[1,2)") + dep("x", "c")
            + "</dependencies>"
        )}
        repository = MavenRepository(URL, make_fetch(files))
        self.assertEqual(names(repository, "g:a:1"), ["x:b", "x:c"])

    def test_models_cached(self):
        """Один и тот же POM скачивается один раз."""
        fetch = mock.Mock(return_value=pom(""))
        repository = MavenRepository(URL, fetch)
        repository.direct_dependencies("g:a:1")
        repository.direct_dependencies("g:a:1")
        fetch.assert_called_once()

    def test_missing_package(self):
        """Отсутствующий пакет - ошибка репозитория."""
        repository = MavenRepository(URL, make_fetch({}))
        with self.assertRaisesRegex(RepositoryError, "HTTP 404"):
            repository.direct_dependencies("g:a:1")


class FetchUrlTest(unittest.TestCase):
    """Проверка обработки сетевых ошибок."""

    def test_http_error(self):
        """Ответ с ошибкой HTTP сообщается с кодом."""
        error = HTTPError(URL, 500, "error", {}, None)
        self.addCleanup(error.close)
        with mock.patch("depgraph.repository.urlopen", side_effect=error):
            with self.assertRaisesRegex(RepositoryError, "HTTP 500"):
                fetch_url(URL)

    def test_network_error(self):
        """Недоступный адрес сообщается как ошибка репозитория."""
        error = URLError("no route")
        with mock.patch("depgraph.repository.urlopen", side_effect=error):
            with self.assertRaisesRegex(RepositoryError, "no route"):
                fetch_url(URL)


class ShowDirectTest(unittest.TestCase):
    """Проверка вывода прямых зависимостей."""

    def run_action(self, body):
        """Выполнить действие direct для тестового POM."""
        files = {pom_url("g", "a", "1"): pom(body)}
        repository = MavenRepository(URL, make_fetch(files))
        config = Config("g:a:1", URL, "real")
        target = "depgraph.actions.create_repository"
        with mock.patch(target, return_value=repository):
            return show_direct(config)

    def test_output(self):
        """Выводятся все зависимости с областью."""
        text = self.run_action(
            "<dependencies>"
            + dep("x", "b", "2")
            + dep("x", "c", "3", "<scope>test</scope>"
                                 "<optional>true</optional>")
            + "</dependencies>"
        )
        self.assertEqual(text.splitlines(), [
            "direct dependencies of g:a:1:",
            "x:b:2 (compile)",
            "x:c:3 (test, optional)",
        ])

    def test_no_dependencies(self):
        """Отсутствие зависимостей сообщается явно."""
        self.assertIn("no direct dependencies", self.run_action(""))


class MainRepositoryErrorTest(unittest.TestCase):
    """Проверка кода завершения при ошибке репозитория."""

    def test_error_code(self):
        """Ошибка репозитория - сообщение и код 1."""
        err = io.StringIO()
        target = "depgraph.repository.urlopen"
        with mock.patch(target, side_effect=URLError("down")):
            with contextlib.redirect_stderr(err):
                code = main(["--package", "g:a:1", "--repo", URL])
        self.assertEqual(code, 1)
        self.assertIn("error: cannot download", err.getvalue())


if __name__ == "__main__":
    unittest.main()
