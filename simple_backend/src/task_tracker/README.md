### ❌ Недостатки хранения данных в оперативной памяти:

1.  **Недолговечность (Volatility):** Все задачи полностью теряются при перезапуске сервера, сбое или завершении работы приложения, так как оперативная память энергозависима.
2.  **Отсутствие горизонтального масштабирования:** При запуске нескольких экземпляров приложения (для распределения нагрузки) каждый экземпляр будет иметь свой собственный изолированный список задач. Это приводит к непоследовательности данных и непредсказуемому поведению для пользователей.
3.  **Ограниченный объем:** Объем хранимых данных напрямую ограничен доступной оперативной памятью сервера.
4.  **Проблемы с параллельным доступом:** При одновременном доступе из разных потоков или запросов к общему списку без надлежащей синхронизации могут возникать ошибки и повреждение данных (так называемое "состояние гонки").

## 💾 Этап 2: Хранение данных в файле (tasks.json)

Для решения проблемы недолговечности данных, приложение было модифицировано для сохранения информации о задачах в локальном JSON-файле (`tasks.json`).

### ✅ Что улучшилось после перехода на файловое хранение?

*   **Постоянство данных (Persistence):** Главное улучшение заключается в том, что задачи теперь не теряются после перезапуска сервера. Они надежно сохраняются на диске.

### ⚠️ Избавились ли мы от хранения состояния?

**Нет.** Приложение по-прежнему является **stateful** (сохраняющим состояние). Его поведение по-прежнему зависит от внешнего ресурса — теперь это файл на диске. Проблема с горизонтальным масштабированием остается актуальной:

*   Если запустить несколько экземпляров приложения, они все будут пытаться одновременно читать и записывать в один и тот же файл. Это неизбежно приведет к конфликтам данных, их потере или повреждению (классическое "состояние гонки"). Текущая реализация не включает механизмов блокировки на уровне файловой системы или базы данных, необходимых для безопасного параллельного доступа.

### 💡 Альтернативные подходы к хранению данных:

Для создания более надежных, масштабируемых и по-настоящему **stateless** backend-приложений обычно используют следующие решения:

1.  **Реляционные Базы Данных (SQL):**
    *   **Преимущества:** Гарантии целостности данных (ACID-транзакции), строгая схема, мощные возможности запросов SQL. Отлично подходят для данных со сложными связями.
    *   **Недостатки:** Требуют более строгой схемы, могут быть сложнее в настройке и горизонтальном масштабировании.
2.  **Нереляционные Базы Данных (NoSQL):**
    *   **Преимущества:** Гибкая схема данных, часто лучше масштабируются горизонтально, высокая производительность для определенных типов операций.
    *   **Недостатки:** Могут иметь более слабые гарантии согласованности данных по сравнению с SQL.
3.  **Облачные Сервисы / Внешние API для хранения данных:**
    *   **Преимущества:** Полностью перекладывают ответственность за хранение, доступность и масштабирование на сторонний сервис. Это основной способ создания по-настоящему **stateless** бэкенда.
    *   **Недостатки:** Зависимость от внешнего провайдера, возможные сетевые задержки, потенциальные затраты.

## 🏁 Этап 3: Проблема конкурентного доступа и "Состояние гонки" (Race Condition)

Несмотря на переход к stateless-архитектуре с использованием внешнего сервиса (`jsonbin.io`), в проекте осталась фундаментальная проблема, связанная с одновременным доступом к данным.


Чтобы решить эту проблему можно уставновить в проект БД например PostgreSQL.

