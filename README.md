# Визуализатор графа зависимостей Maven (вариант 18)

## Общее описание

Консольное (CLI) приложение на Python для анализа зависимостей пакетов
Maven. Менеджеры пакетов и сторонние библиотеки для получения
зависимостей не используются. Текущее состояние:

- **Этап 1. Минимальный прототип с конфигурацией** — параметры
  командной строки, вывод параметров, обработка ошибок.
- **Этап 2. Сбор данных** — получение прямых зависимостей пакета
  из репозитория Maven по URL.
- **Этап 3. Основные операции** — граф зависимостей с учетом
  транзитивности (BFS с рекурсией), циклы, тестовый репозиторий.
- **Этап 4. Дополнительные операции** — обратные зависимости пакета.

Внешних зависимостей нет, требуется Python 3.8+.

## Параметры командной строки

```
python src/main.py --package NAME --repo URL_OR_PATH [--mode MODE] [--action ACTION]
```

| Параметр | Описание |
|---|---|
| `--package NAME` | Имя анализируемого пакета: `group:artifact[:version]`, в тестовом режиме — большие латинские буквы |
| `--repo URL_OR_PATH` | URL-адрес репозитория (`http`, `https`) или путь к файлу тестового репозитория |
| `--mode MODE` | Режим работы: `real` (по умолчанию) или `test` |
| `--action ACTION` | Что сделать: `config` — вывести параметры в формате ключ-значение, `direct` — вывести прямые зависимости, `graph` — вывести граф зависимостей (по умолчанию), `reverse` — вывести обратные зависимости |

## Получение данных из Maven

Менеджеры пакетов и сторонние библиотеки не используются: файлы
скачиваются модулем `urllib`, XML разбирается модулем
`xml.etree.ElementTree`.

1. Если версия пакета не указана, последняя версия берется из файла
   `maven-metadata.xml`.
2. Скачивается POM-файл
   `<repo>/<group>/<artifact>/<version>/<artifact>-<version>.pom`.
3. Рекурсивно скачиваются родительские POM: от них наследуются свойства,
   управляемые версии (`dependencyManagement`) и зависимости.
4. Записи `dependencyManagement` с областью `import` подключают
   управляемые версии из BOM.
5. В зависимости подставляются свойства `${...}`, а недостающие версия
   и область берутся из управляемых версий.

Загруженные модели кешируются на время работы программы.

В вывод `direct` попадают все зависимости из POM с их областью.
В граф входят только зависимости, нужные при выполнении пакета:
области `compile` и `runtime`, кроме необязательных (`optional`).

## Построение графа

Граф строится функцией `bfs`: обход в ширину с рекурсией, где один
вызов обрабатывает один уровень. Для всех пакетов текущего уровня
запрашиваются зависимости, а затем функция вызывает себя для следующего
уровня, в который входят только еще не посещенные пакеты.

Поэтому циклические зависимости не приводят к зацикливанию: каждый
пакет обрабатывается один раз. Сами циклы находит функция `find_cycles`
(поиск в глубину) и выводит их отдельно.

Если данные о транзитивной зависимости получить не удалось, выводится
предупреждение `warning: ...`, а пакет остается в графе без зависимостей.
Ошибка для анализируемого пакета прерывает работу.

## Тестовый репозиторий

В режиме `--mode test` вместо URL указывается путь к файлу с описанием
графа. Пакеты называются большими латинскими буквами, пустые строки и
строки с `#` пропускаются. Пакет, упомянутый только как зависимость,
считается пакетом без зависимостей.

```
# пакет: зависимости
A: B C
B: D
C: D
```

| Файл | Случай |
|---|---|
| `repos/simple.txt` | Цепочка |
| `repos/diamond.txt` | Ромб: общая зависимость обходится один раз |
| `repos/cycle.txt` | Два цикла |
| `repos/self_loop.txt` | Пакет зависит сам от себя |
| `repos/forest.txt` | Несвязанные части, имена из нескольких букв |
| `repos/broken.txt` | Файл с ошибкой формата |

## Обратные зависимости

Действие `--action reverse` выводит пакеты, которые зависят от заданного
пакета, напрямую и транзитивно. Ребра всех пакетов репозитория
разворачиваются функцией `reverse_edges`, а затем используется тот же
обход `bfs`, что и для прямого графа. Уровень 1 — прямые зависимые
пакеты, следующие уровни — транзитивные.

Действие работает только в тестовом режиме: в репозитории Maven нет
индекса, который позволял бы узнать, какие пакеты зависят от данного,
а перебрать все пакеты Maven Central невозможно.

## Обработка ошибок

Неверные значения параметров выводятся в stderr, код завершения 2.

| Ситуация | Сообщение |
|---|---|
| Неверное имя пакета | `error: invalid package 'junit': expected group:artifact[:version]` |
| Неверное имя в тестовом режиме | `error: invalid package 'abc': expected capital latin letters in the test mode` |
| Неверный URL | `error: invalid repository URL 'ftp://example.com': expected an http or https address` |
| Неизвестный режим | `error: invalid mode 'fast': expected one of real, test` |
| Нет файла репозитория | `error: repository file not found: 'nope.txt'` |
| Директория вместо файла | `error: repository path is not a file: 'scripts'` |

Ошибки получения данных выводятся в stderr, код завершения 1:

| Ситуация | Сообщение |
|---|---|
| Пакет не найден | `error: cannot download <url>: HTTP 404` |
| Нет сети или адрес недоступен | `error: cannot download <url>: <причина>` |
| Файл поврежден | `error: invalid XML: ...` |
| Файл не является POM | `error: not a POM file: root element <html>` |
| Нет пакета в тестовом репозитории | `error: package Z not found in the test repository` |
| Неверная строка файла | `error: line 3: invalid format: 'b: C'` |
| Пакет описан дважды | `error: line 2: package A is defined twice` |
| `reverse` в реальном режиме | `error: reverse dependencies need the test mode: ...` |

## Сборка и запуск тестов

Сборка не требуется.

```bat
run.bat --package junit:junit --repo https://repo1.maven.org/maven2
run.bat test
```

```sh
./run.sh --package junit:junit --repo https://repo1.maven.org/maven2
./run.sh test
```

Тесты напрямую, из корня проекта:
`python -m unittest discover -s tests -t .`

Демонстрация этапов: `scripts/demo_stage1.bat`,
`scripts/demo_stage2.bat`, `scripts/demo_stage3.bat`,
`scripts/demo_stage4.bat` (или `.sh` в Linux и macOS).

## Примеры использования

```
> python src/main.py --package junit:junit:4.13.2 --repo https://repo1.maven.org/maven2 --action config
package=junit:junit:4.13.2
repo=https://repo1.maven.org/maven2
mode=real
action=config
```

```
> python src/main.py --package junit:junit:4.13.2 --repo https://repo1.maven.org/maven2 --action direct
direct dependencies of junit:junit:4.13.2:
org.hamcrest:hamcrest-core:1.3 (compile)
org.hamcrest:hamcrest-library:1.3 (test)
```

```
> python src/main.py --package A --repo repos/cycle.txt --mode test
dependency graph of A:
levels:
0: A
1: B
2: C, D
3: E
edges:
A -> B
B -> C, D
C -> A
D -> E
E -> D
cycles:
A -> B -> C -> A
D -> E -> D
packages: 5
```

```
> python src/main.py --package E --repo repos/diamond.txt --mode test --action reverse
reverse dependencies of E:
levels:
0: E
1: D
2: B, C
3: A
edges (package <- dependents):
E <- D
D <- B, C
B <- A
C <- A
A <- (none)
dependents: 4
```
