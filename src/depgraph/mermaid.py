"""Визуализация графа зависимостей на языке диаграмм Mermaid."""

import html
import os
import pathlib
import re
import webbrowser

OUTPUT_DIR = "out"
MERMAID_SCRIPT = (
    "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"
)
UNSAFE_NAME_CHARS = re.compile(r"[^\w.-]")
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: sans-serif; margin: 24px; }}
h1 {{ font-size: 20px; }}
</style>
</head>
<body>
<h1>{title}</h1>
<pre class="mermaid">
{diagram}
</pre>
<script src="{script}"></script>
<script>mermaid.initialize({{startOnLoad: true, maxEdges: 2000}});</script>
</body>
</html>
"""


def to_mermaid(edges):
    """Сформировать текст диаграммы Mermaid по ребрам графа.

    Имена пакетов содержат символы, недопустимые в идентификаторах
    Mermaid, поэтому узлы получают номера, а имя становится подписью.
    """
    ids = {node: f"n{number}" for number, node in enumerate(edges)}
    lines = ["graph TD"]
    lines.extend(f'    {ids[node]}["{node}"]' for node in edges)
    lines.extend(
        f"    {ids[node]} --> {ids[child]}"
        for node, children in edges.items()
        for child in children
    )
    return "\n".join(lines)


def render_page(title, diagram):
    """Сформировать HTML-страницу с диаграммой."""
    return PAGE.format(
        title=html.escape(title),
        diagram=html.escape(diagram),
        script=MERMAID_SCRIPT,
    )


def page_path(package):
    """Построить путь к файлу страницы для пакета."""
    name = UNSAFE_NAME_CHARS.sub("_", package)
    return os.path.join(OUTPUT_DIR, f"graph_{name}.html")


def save_page(package, diagram):
    """Сохранить страницу с диаграммой и вернуть путь к ней."""
    path = page_path(package)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(render_page(f"Dependencies of {package}", diagram))
    return path


def open_page(path):
    """Открыть страницу с изображением графа в браузере."""
    return webbrowser.open(pathlib.Path(path).resolve().as_uri())
