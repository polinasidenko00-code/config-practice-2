"""Разбор и проверка параметров командной строки."""

import argparse
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from depgraph.errors import ConfigError

REAL_MODE = "real"
TEST_MODE = "test"
MODES = (REAL_MODE, TEST_MODE)
ACTION_NAMES = ("config", "direct", "graph", "reverse", "mermaid")
DEFAULT_ACTION = "graph"
URL_SCHEMES = ("http", "https")
MAVEN_PACKAGE = re.compile(r"[\w.-]+:[\w.-]+(:[\w.+-]+)?")
TEST_PACKAGE = re.compile(r"[A-Z]+")


@dataclass(frozen=True)
class Config:
    """Параметры запуска, заданные пользователем."""

    package: str
    repository: str
    mode: str
    action: str = DEFAULT_ACTION
    open_browser: bool = True


def build_parser():
    """Создать парсер параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Dependency graph visualizer for Maven packages.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--package", required=True, metavar="NAME",
        help="package to analyze: group:artifact[:version], "
             "or capital latin letters in the test mode",
    )
    parser.add_argument(
        "--repo", required=True, metavar="URL_OR_PATH",
        help="repository URL, or a path to a test repository file",
    )
    parser.add_argument(
        "--mode", default=REAL_MODE, metavar="MODE",
        help="repository mode: real (default) or test",
    )
    parser.add_argument(
        "--action", default=DEFAULT_ACTION, metavar="ACTION",
        help=f"what to do: {', '.join(ACTION_NAMES)} "
             f"(default: {DEFAULT_ACTION})",
    )
    parser.add_argument(
        "--no-browser", dest="open_browser", action="store_false",
        help="do not open the image of the graph in a browser",
    )
    return parser


def validate_mode(mode):
    """Проверить режим работы с репозиторием."""
    if mode not in MODES:
        raise ConfigError(
            f"invalid mode '{mode}': expected one of {', '.join(MODES)}"
        )


def validate_action(action):
    """Проверить название действия."""
    if action not in ACTION_NAMES:
        raise ConfigError(
            f"invalid action '{action}': "
            f"expected one of {', '.join(ACTION_NAMES)}"
        )


def validate_package(package, mode):
    """Проверить имя пакета с учетом режима работы."""
    if mode == TEST_MODE:
        if not TEST_PACKAGE.fullmatch(package):
            raise ConfigError(
                f"invalid package '{package}': "
                "expected capital latin letters in the test mode"
            )
    elif not MAVEN_PACKAGE.fullmatch(package):
        raise ConfigError(
            f"invalid package '{package}': "
            "expected group:artifact[:version]"
        )


def validate_url(url):
    """Проверить адрес реального репозитория."""
    parts = urlparse(url)
    if parts.scheme not in URL_SCHEMES or not parts.netloc:
        raise ConfigError(
            f"invalid repository URL '{url}': "
            "expected an http or https address"
        )


def validate_path(path):
    """Проверить путь к файлу тестового репозитория."""
    if not os.path.exists(path):
        raise ConfigError(f"repository file not found: '{path}'")
    if not os.path.isfile(path):
        raise ConfigError(f"repository path is not a file: '{path}'")


def load_config(argv=None):
    """Получить проверенные параметры из командной строки.

    argv - список аргументов; None означает sys.argv[1:].
    Выбрасывает ConfigError при неверном значении параметра.
    """
    args = build_parser().parse_args(argv)
    validate_mode(args.mode)
    validate_action(args.action)
    validate_package(args.package, args.mode)
    if args.mode == TEST_MODE:
        validate_path(args.repo)
    else:
        validate_url(args.repo)
    return Config(
        args.package, args.repo, args.mode, args.action, args.open_browser
    )


def format_config(config):
    """Сформировать вывод всех параметров в формате ключ-значение."""
    return "\n".join([
        f"package={config.package}",
        f"repo={config.repository}",
        f"mode={config.mode}",
        f"action={config.action}",
        f"open_browser={config.open_browser}",
    ])
