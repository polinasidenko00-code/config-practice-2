# Визуализатор графа зависимостей Maven (вариант 18)

## Общее описание

Консольное (CLI) приложение на Python для анализа зависимостей пакетов
Maven. Менеджеры пакетов и сторонние библиотеки для получения
зависимостей не используются. Текущее состояние:

- **Этап 1. Минимальный прототип с конфигурацией** — параметры
  командной строки, вывод параметров, обработка ошибок.
- **Этап 2. Сбор данных** — получение прямых зависимостей пакета
  из репозитория Maven по URL.

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
| `--action ACTION` | Что сделать: `config` — вывести параметры в формате ключ-значение, `direct` — вывести прямые зависимости (по умолчанию) |

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
`scripts/demo_stage2.bat` (или `.sh` в Linux и macOS).

## Примеры использования

```
> python src/main.py --package junit:junit:4.13.2 --repo https://repo1.maven.org/maven2 --action config
package=junit:junit:4.13.2
repo=https://repo1.maven.org/maven2
mode=real
action=config
```

```
> python src/main.py --package junit:junit:4.13.2 --repo https://repo1.maven.org/maven2
direct dependencies of junit:junit:4.13.2:
org.hamcrest:hamcrest-core:1.3 (compile)
org.hamcrest:hamcrest-library:1.3 (test)
```
