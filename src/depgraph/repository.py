"""Источники данных о зависимостях пакетов."""

import re
from dataclasses import dataclass, field, replace
from typing import Dict, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from depgraph.errors import RepositoryError
from depgraph.pom import (
    PomDependency,
    interpolate,
    parse_latest_version,
    parse_pom,
)

DEFAULT_SCOPE = "compile"
RUNTIME_SCOPES = ("compile", "runtime")
IMPORT_SCOPE = "import"
USER_AGENT = "depgraph/1.0"
TIMEOUT_SECONDS = 30
RANGE_PREFIXES = ("[", "(")
PLACEHOLDER = "${"
OPTIONAL_VALUE = "true"
COMMENT_PREFIX = "#"
GRAPH_LINE = re.compile(r"([A-Z]+)\s*:((?:\s*[A-Z]+)*)\s*")


@dataclass(frozen=True)
class Dependency:
    """Прямая зависимость пакета."""

    name: str
    scope: str = DEFAULT_SCOPE
    optional: bool = False

    @property
    def transitive(self):
        """Переходит ли зависимость в граф пакета при выполнении."""
        return self.scope in RUNTIME_SCOPES and not self.optional


@dataclass
class Model:
    """Итоговая модель пакета с учетом родительских POM."""

    properties: Dict[str, str] = field(default_factory=dict)
    managed: Dict[Tuple[str, str], PomDependency] = field(
        default_factory=dict
    )
    dependencies: List[PomDependency] = field(default_factory=list)


def fetch_url(url):
    """Скачать файл по адресу и вернуть его содержимое в байтах."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.read()
    except HTTPError as error:
        raise RepositoryError(
            f"cannot download {url}: HTTP {error.code}"
        ) from None
    except OSError as error:
        raise RepositoryError(f"cannot download {url}: {error}") from None


def clean_version(version):
    """Вернуть точную версию или None, если она не определена."""
    if not version or PLACEHOLDER in version:
        return None
    if version.startswith(RANGE_PREFIXES):
        return None
    return version


def split_package(package):
    """Разделить имя пакета на (группа, артефакт, версия или None)."""
    group, artifact, *version = package.split(":")
    return group, artifact, version[0] if version else None


class MavenRepository:
    """Репозиторий Maven, доступный по URL.

    fetch - функция скачивания файла; в тестах ее подменяют.
    Загруженные модели кешируются, чтобы не скачивать POM повторно.
    """

    def __init__(self, url, fetch=fetch_url):
        """Запомнить адрес репозитория и функцию скачивания."""
        self.url = url.rstrip("/")
        self.fetch = fetch
        self.models = {}

    def artifact_url(self, group, artifact):
        """Построить адрес каталога артефакта в репозитории."""
        return f"{self.url}/{group.replace('.', '/')}/{artifact}"

    def latest_version(self, group, artifact):
        """Узнать последнюю версию артефакта."""
        url = self.artifact_url(group, artifact)
        return parse_latest_version(
            self.fetch(f"{url}/maven-metadata.xml")
        )

    def load_pom(self, group, artifact, version):
        """Скачать и разобрать POM-файл версии артефакта."""
        url = self.artifact_url(group, artifact)
        return parse_pom(
            self.fetch(f"{url}/{version}/{artifact}-{version}.pom")
        )

    def load_model(self, group, artifact, version):
        """Построить модель пакета с учетом его родителей."""
        key = (group, artifact, version)
        if key not in self.models:
            pom = self.load_pom(group, artifact, version)
            parent = self.load_model(*pom.parent) if pom.parent else Model()
            self.models[key] = self.merge(pom, parent, key)
        return self.models[key]

    def merge(self, pom, parent, key):
        """Объединить POM с моделью родителя."""
        group, artifact, version = key
        properties = {**parent.properties, **pom.properties}
        for prefix in ("project", "pom"):
            properties[f"{prefix}.groupId"] = pom.group or group
            properties[f"{prefix}.artifactId"] = artifact
            properties[f"{prefix}.version"] = pom.version or version
        if pom.parent:
            properties["project.parent.version"] = pom.parent[-1]
        model = Model(
            properties=properties,
            managed=dict(parent.managed),
            dependencies=parent.dependencies + pom.dependencies,
        )
        for item in pom.managed:
            self.add_managed(model, item)
        return model

    def add_managed(self, model, item):
        """Добавить запись dependencyManagement в модель.

        Запись с областью import подключает управляемые версии
        другого POM (BOM); явные записи пакета имеют приоритет.
        """
        item = resolve_item(item, model.properties)
        if item.scope != IMPORT_SCOPE:
            model.managed[(item.group, item.artifact)] = item
            return
        imported = self.load_model(item.group, item.artifact, item.version)
        for key, value in imported.managed.items():
            model.managed.setdefault(key, value)

    def direct_dependencies(self, package):
        """Вернуть список прямых зависимостей пакета."""
        group, artifact, version = split_package(package)
        version = version or self.latest_version(group, artifact)
        model = self.load_model(group, artifact, version)
        return [effective(item, model) for item in model.dependencies]


def resolve_item(item, properties):
    """Подставить свойства во все поля зависимости."""
    return PomDependency(
        group=interpolate(item.group, properties),
        artifact=interpolate(item.artifact, properties),
        version=interpolate(item.version, properties),
        scope=interpolate(item.scope, properties),
        optional=interpolate(item.optional, properties),
    )


def effective(item, model):
    """Получить зависимость с учетом свойств и управляемых версий."""
    item = resolve_item(item, model.properties)
    managed = model.managed.get((item.group, item.artifact))
    if managed is not None:
        managed = resolve_item(managed, model.properties)
        item = replace(
            item,
            version=item.version or managed.version,
            scope=item.scope or managed.scope,
        )
    name = f"{item.group}:{item.artifact}"
    version = clean_version(item.version)
    if version:
        name = f"{name}:{version}"
    return Dependency(
        name=name,
        scope=item.scope or DEFAULT_SCOPE,
        optional=item.optional == OPTIONAL_VALUE,
    )


def parse_graph(text):
    """Разобрать описание графа тестового репозитория.

    Каждая строка имеет вид "A: B C", пакеты называются большими
    латинскими буквами. Пустые строки и строки с # пропускаются.
    Пакет, который упомянут только как зависимость, считается
    пакетом без зависимостей.
    """
    graph = {}
    defined = set()
    for number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue
        match = GRAPH_LINE.fullmatch(line)
        if match is None:
            raise RepositoryError(f"line {number}: invalid format: '{line}'")
        package, dependencies = match.group(1), match.group(2).split()
        if package in defined:
            raise RepositoryError(
                f"line {number}: package {package} is defined twice"
            )
        defined.add(package)
        graph[package] = dependencies
        for dependency in dependencies:
            graph.setdefault(dependency, [])
    return graph


class FileRepository:
    """Тестовый репозиторий, описанный текстовым файлом."""

    def __init__(self, path):
        """Прочитать файл с описанием графа."""
        try:
            with open(path, encoding="utf-8-sig") as file:
                self.graph = parse_graph(file.read())
        except (OSError, UnicodeDecodeError) as error:
            raise RepositoryError(
                f"cannot read repository file '{path}': {error}"
            ) from None

    def direct_dependencies(self, package):
        """Вернуть список прямых зависимостей пакета."""
        if package not in self.graph:
            raise RepositoryError(
                f"package {package} not found in the test repository"
            )
        return [Dependency(name) for name in self.graph[package]]
