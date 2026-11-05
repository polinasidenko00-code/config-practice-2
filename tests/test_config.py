"""Тесты параметров командной строки."""

import contextlib
import io
import os
import tempfile
import unittest

from depgraph.config import format_config, load_config
from depgraph.errors import ConfigError
from main import main

URL = "https://repo1.maven.org/maven2"
PACKAGE = "junit:junit:4.13.2"


def real_args(package=PACKAGE, repo=URL):
    """Собрать аргументы запуска с реальным репозиторием."""
    return ["--package", package, "--repo", repo]


class LoadConfigTest(unittest.TestCase):
    """Проверка значений параметров."""

    def test_real_mode_by_default(self):
        """Без --mode используется реальный репозиторий."""
        config = load_config(real_args())
        self.assertEqual(config.mode, "real")
        self.assertEqual(config.package, PACKAGE)
        self.assertEqual(config.repository, URL)

    def test_package_without_version(self):
        """Версия пакета необязательна."""
        self.assertEqual(
            load_config(real_args("junit:junit")).package, "junit:junit"
        )

    def test_test_mode(self):
        """Тестовый режим принимает файл и большие буквы."""
        with tempfile.NamedTemporaryFile(delete=False) as file:
            self.addCleanup(os.remove, file.name)
        config = load_config(
            ["--package", "AB", "--repo", file.name, "--mode", "test"]
        )
        self.assertEqual(config.package, "AB")

    def test_invalid_mode(self):
        """Неизвестный режим - ошибка."""
        with self.assertRaisesRegex(ConfigError, "invalid mode"):
            load_config(real_args() + ["--mode", "fast"])

    def test_invalid_action(self):
        """Неизвестное действие - ошибка."""
        with self.assertRaisesRegex(ConfigError, "invalid action"):
            load_config(real_args() + ["--action", "dance"])

    def test_invalid_package(self):
        """Неверные имена пакета - ошибка."""
        for package in ("", "junit", "a:b:c:d", "a b:c"):
            with self.assertRaisesRegex(ConfigError, "invalid package"):
                load_config(real_args(package))

    def test_invalid_url(self):
        """Адрес без http или https - ошибка."""
        for url in ("", "repo", "ftp://host/repo", "https://"):
            with self.assertRaisesRegex(ConfigError, "invalid repository"):
                load_config(real_args(repo=url))

    def test_invalid_test_package(self):
        """В тестовом режиме имя - только большие буквы."""
        with tempfile.NamedTemporaryFile(delete=False) as file:
            self.addCleanup(os.remove, file.name)
        for package in ("a", "A1", "junit:junit"):
            with self.assertRaisesRegex(ConfigError, "capital latin"):
                load_config(
                    ["--package", package, "--repo", file.name,
                     "--mode", "test"]
                )

    def test_missing_file(self):
        """Отсутствующий файл репозитория - ошибка."""
        with self.assertRaisesRegex(ConfigError, "not found"):
            load_config(
                ["--package", "A", "--repo", "nope.txt", "--mode", "test"]
            )

    def test_directory_instead_of_file(self):
        """Директория вместо файла - ошибка."""
        with tempfile.TemporaryDirectory() as path:
            with self.assertRaisesRegex(ConfigError, "not a file"):
                load_config(
                    ["--package", "A", "--repo", path, "--mode", "test"]
                )

    def test_missing_required_option(self):
        """Обязательный параметр не задан - завершение с ошибкой."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                load_config(["--package", PACKAGE])


class FormatConfigTest(unittest.TestCase):
    """Проверка вывода параметров."""

    def test_key_value_format(self):
        """Все параметры выводятся в формате ключ-значение."""
        text = format_config(load_config(real_args()))
        self.assertEqual(
            text.splitlines(),
            [f"package={PACKAGE}", f"repo={URL}", "mode=real",
             "action=graph"],
        )


class MainTest(unittest.TestCase):
    """Проверка точки входа."""

    def run_main(self, argv):
        """Запустить main, вернуть (код, вывод, ошибки)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out):
            with contextlib.redirect_stderr(err):
                code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_config_error_code(self):
        """Ошибка параметра - сообщение и код 2."""
        code, _out, err = self.run_main(real_args("junit"))
        self.assertEqual(code, 2)
        self.assertIn("error: invalid package", err)


if __name__ == "__main__":
    unittest.main()
