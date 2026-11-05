# Визуализатор графа зависимостей Maven (вариант 18)

## Общее описание

Консольное (CLI) приложение на Python для анализа зависимостей пакетов
Maven. Менеджеры пакетов и сторонние библиотеки для получения
зависимостей не используются. Текущее состояние:

- **Этап 1. Минимальный прототип с конфигурацией** — параметры
  командной строки, вывод параметров, обработка ошибок.

Внешних зависимостей нет, требуется Python 3.8+.

## Параметры командной строки

```
python src/main.py --package NAME --repo URL_OR_PATH [--mode MODE]
```

| Параметр | Описание |
|---|---|
| `--package NAME` | Имя анализируемого пакета: `group:artifact[:version]`, в тестовом режиме — большие латинские буквы |
| `--repo URL_OR_PATH` | URL-адрес репозитория (`http`, `https`) или путь к файлу тестового репозитория |
| `--mode MODE` | Режим работы: `real` (по умолчанию) или `test` |

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

Демонстрация этапа: `scripts/demo_stage1.bat` или
`scripts/demo_stage1.sh`.

## Пример использования

```
> python src/main.py --package junit:junit:4.13.2 --repo https://repo1.maven.org/maven2
package=junit:junit:4.13.2
repo=https://repo1.maven.org/maven2
mode=real
```
