# Сравнение со штатным инструментом Maven

Для трех пакетов результат программы сравнивался с выводом штатного
инструмента `mvn dependency:tree` (Apache Maven 3.9.9, плагин
maven-dependency-plugin 3.6.1). Для запуска Maven использовался пустой
проект с одной зависимостью от проверяемого пакета.

| Пакет | Пакетов у программы | Пакетов у Maven | Результат |
|---|---|---|---|
| `junit:junit:4.13.2` | 2 | 2 | Совпадает |
| `com.google.guava:guava:33.0.0-jre` | 7 | 7 | Совпадает |
| `com.squareup.okhttp3:okhttp:4.12.0` | 12 | 8 | Есть расхождение |

Изображения графов: [junit](examples/junit.mmd),
[guava](examples/guava.mmd), [okhttp](examples/okhttp.mmd).

## junit и guava

Наборы пакетов и версий совпадают полностью.

```
\- junit:junit:jar:4.13.2:compile
   \- org.hamcrest:hamcrest-core:jar:1.3:compile
```

```
\- com.google.guava:guava:jar:33.0.0-jre:compile
   +- com.google.guava:failureaccess:jar:1.0.2:compile
   +- com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
   +- com.google.code.findbugs:jsr305:jar:3.0.2:compile
   +- org.checkerframework:checker-qual:jar:3.41.0:compile
   +- com.google.errorprone:error_prone_annotations:jar:2.23.0:compile
   \- com.google.j2objc:j2objc-annotations:jar:2.8:compile
```

## okhttp

Вывод Maven:

```
\- com.squareup.okhttp3:okhttp:jar:4.12.0:compile
   +- com.squareup.okio:okio:jar:3.6.0:compile
   |  \- com.squareup.okio:okio-jvm:jar:3.6.0:compile
   |     \- org.jetbrains.kotlin:kotlin-stdlib-common:jar:1.9.10:compile
   \- org.jetbrains.kotlin:kotlin-stdlib-jdk8:jar:1.8.21:compile
      +- org.jetbrains.kotlin:kotlin-stdlib:jar:1.8.21:compile
      |  \- org.jetbrains:annotations:jar:13.0:compile
      \- org.jetbrains.kotlin:kotlin-stdlib-jdk7:jar:1.8.21:compile
```

Только у программы есть четыре пакета:

- `org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.10`
- `org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.9.10`
- `org.jetbrains.kotlin:kotlin-stdlib:1.9.10`
- `org.jetbrains.kotlin:kotlin-stdlib-common:1.8.21`

Пакетов, которые есть только у Maven, нет.

**Причина расхождения.** `okio-jvm` требует Kotlin версии 1.9.10, а
`okhttp` — версии 1.8.21. Maven решает такие конфликты: для каждого
артефакта остается одна версия, ближайшая к корню дерева, а при равном
расстоянии — объявленная первой. Поэтому `kotlin-stdlib-jdk8:1.8.21`
(глубина 1) вытесняет `1.9.10` (глубина 3), а вместе с вытесненной версией
из дерева исчезают и ее зависимости. `kotlin-stdlib-common` встречается
на одной глубине в двух версиях, и выигрывает `1.9.10`: путь через `okio`
объявлен первым.

Программа конфликты версий не разрешает и показывает граф всех
объявленных зависимостей. Узел графа — это пакет вместе с версией, и
каждая версия обходится отдельно. Такой граф показывает, что заявлено в
POM-файлах, а Maven показывает, что попадет в сборку.

## Другие возможные причины расхождений

| Возможность Maven | Maven | Программа |
|---|---|---|
| Конфликт версий | Остается одна версия | Показываются все версии |
| `exclusions` | Исключенная зависимость не попадает в дерево | Исключения не учитываются |
| Профили (`profiles`) | Могут добавлять зависимости и свойства | Не учитываются |
| Области при транзитивности | Вычисляются по таблице областей | Учитываются только `compile` и `runtime` |
| Циклы | Повторный пакет в дерево не попадает | Цикл выводится в отчете `cycles` |
| Диапазоны версий | Выбирается подходящая версия | Используется последняя версия |
