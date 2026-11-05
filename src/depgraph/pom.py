"""Разбор файлов описания пакетов Maven (POM)."""

import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from depgraph.errors import RepositoryError

PROPERTY = re.compile(r"\$\{([^}]+)\}")
MAX_SUBSTITUTIONS = 10
NAMESPACE_END = "}"


@dataclass(frozen=True)
class PomDependency:
    """Зависимость в том виде, как она записана в POM."""

    group: str
    artifact: str
    version: Optional[str] = None
    scope: Optional[str] = None
    optional: Optional[str] = None


@dataclass
class Pom:
    """Содержимое одного POM-файла."""

    group: Optional[str] = None
    artifact: Optional[str] = None
    version: Optional[str] = None
    parent: Optional[Tuple[str, str, str]] = None
    properties: Dict[str, str] = field(default_factory=dict)
    managed: List[PomDependency] = field(default_factory=list)
    dependencies: List[PomDependency] = field(default_factory=list)


def parse_xml(data):
    """Разобрать XML и убрать пространства имен из имен тегов."""
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        raise RepositoryError(f"invalid XML: {error}") from None
    for element in root.iter():
        element.tag = element.tag.rpartition(NAMESPACE_END)[2]
    return root


def text_of(element, path):
    """Вернуть текст дочернего элемента или None, если его нет."""
    if element is None:
        return None
    text = element.findtext(path)
    return text.strip() if text else None


def parse_dependency(element):
    """Разобрать элемент dependency."""
    return PomDependency(
        group=text_of(element, "groupId"),
        artifact=text_of(element, "artifactId"),
        version=text_of(element, "version"),
        scope=text_of(element, "scope"),
        optional=text_of(element, "optional"),
    )


def parse_dependencies(element):
    """Разобрать все зависимости из элемента dependencies."""
    if element is None:
        return []
    return [parse_dependency(item) for item in element.findall("dependency")]


def parse_parent(root):
    """Вернуть (группа, артефакт, версия) родителя или None."""
    parent = root.find("parent")
    if parent is None:
        return None
    return (
        text_of(parent, "groupId"),
        text_of(parent, "artifactId"),
        text_of(parent, "version"),
    )


def parse_properties(root):
    """Вернуть словарь свойств из элемента properties."""
    element = root.find("properties")
    if element is None:
        return {}
    return {item.tag: (item.text or "").strip() for item in element}


def parse_pom(data):
    """Разобрать POM-файл из байтов в объект Pom.

    Выбрасывает RepositoryError, если XML некорректен или
    корневой элемент не project.
    """
    root = parse_xml(data)
    if root.tag != "project":
        raise RepositoryError(f"not a POM file: root element <{root.tag}>")
    return Pom(
        group=text_of(root, "groupId"),
        artifact=text_of(root, "artifactId"),
        version=text_of(root, "version"),
        parent=parse_parent(root),
        properties=parse_properties(root),
        managed=parse_dependencies(
            root.find("dependencyManagement/dependencies")
        ),
        dependencies=parse_dependencies(root.find("dependencies")),
    )


def parse_latest_version(data):
    """Получить последнюю версию из файла maven-metadata.xml."""
    root = parse_xml(data)
    versions = root.findall("versioning/versions/version")
    version = text_of(root, "versioning/release")
    version = version or text_of(root, "versioning/latest")
    if not version and versions:
        version = versions[-1].text
    if not version:
        raise RepositoryError("no versions in maven-metadata.xml")
    return version.strip()


def interpolate(value, properties):
    """Подставить значения свойств ${...} в строку.

    Неизвестные свойства остаются без изменений. Значение может
    ссылаться на другое свойство, поэтому подстановка повторяется.
    """
    for _ in range(MAX_SUBSTITUTIONS):
        if value is None or not PROPERTY.search(value):
            break
        value = PROPERTY.sub(
            lambda match: properties.get(match.group(1), match.group(0)),
            value,
        )
    return value
