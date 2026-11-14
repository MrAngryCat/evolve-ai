# Project Evolve AI

**Project status:** phase 00 foundation implemented; see `docs/PROGRESS.md` for verification and review status.  
**Plan version:** 1.0 — 2026-11-13.  
**Target:** Windows; local-first; no new mandatory paid services or hardware.

Evolve AI is a *single* user-directed autonomous software agent with two or more interchangeable local language models, one shared external memory, a goal/task journal, supervised tools, and a measured code-improvement workflow. Its long-term objective is to learn new *software capabilities*, rather than to claim consciousness, guaranteed recursive intelligence amplification, or magical self-training of a base model.

## People and roles

- **Owner:** sets goals, budgets and permissions; approves phase gates and impactful changes.
- **ChatGPT:** architect/planner/reviewer; prepares Codex tasks, evaluates evidence and adjusts the roadmap.
- **Codex:** implementer; writes code, tests, documentation, and phase reports within approved scope.
- **Evolve AI (future running system):** executes bounded autonomous tasks, saves progress, proposes/test changes; does not independently grant itself more privileges.

## Hard constraints

1. No paid API or subscription dependency; no purchase/auto-charge; optional free-tier cloud services only after explicit opt-in and hard-disable when free quotas are reached.
2. Local operation without cloud connectivity, with offline tests for the base system.
3. Single shared persistent state across models; model weights do not share their internal memories.
4. Safety core, access policy and audit log are protected from self-modification.
5. All untrusted code executes in an isolated, resource-limited workspace; sensitive actions require human approval.
6. Support pause, stop, explicit quotas, rollback and recovery after restart.
7. Only advance phases after passing acceptance tests and owner review.
8. Preserve provenance and licenses for reused open-source components.

## Known PC and candidates

- CPU: AMD Ryzen 7 7800X3D; GPU: Radeon RX 6700 XT (12 GB VRAM); RAM: 32 GB DDR5.
- Windows version, free disk, and available Python/toolchain: **verify, never assume**.
- Local inference first candidate: llama.cpp with Vulkan; benchmark must validate compatibility.
- Fast candidate: Qwen3.5-9B (GGUF, appropriate quantization).
- Large candidate: Qwen3.5-35B-A3B or newer supported alternative; may require RAM offload and be slow. **Do not assume working Vulkan compatibility**.
- No model is downloaded/installed in phase 00.

## Repository guidance

- `AGENTS.md`: binding project operating rules for Codex.
- `docs/PROJECT_CHARTER.md`: fixed vision, scope and success criteria.
- `docs/ROADMAP.md`: full staged plan with gates.
- `docs/ARCHITECTURE.md`: target modules, boundaries and data flows.
- `docs/SECURITY_AND_BUDGET.md`: safety and zero-fee controls.
- `docs/MODEL_EVALUATION.md`: model benchmark protocol and fallback.
- `docs/DECISIONS.md`: decisions/ADRs.
- `docs/PROGRESS.md`: authoritative implementation status.
- `docs/THIRD_PARTY.md`: license register and integration policy.
- `prompts/PHASE_00_CODEX.md`: first implementation prompt.
- `prompts/NEXT_PHASE_TEMPLATE.md`: repeatable handoff prompt.

## Этап 00: запуск в Windows PowerShell

Нужен уже установленный **Python 3.12+**. Запуск из исходников не требует
`pip install`, API-ключей, интернета, GPU или скачивания моделей. Git нужен
для истории изменений и получения репозитория, но не для работы CLI.

Из каталога проекта:

```powershell
Set-Location A:\evolve-ai
python --version
python -m evolve --help
python -m evolve doctor
python -m evolve status
python -m unittest discover -s tests -v
```

Если `python` открывает Microsoft Store или сообщает об ошибке доступа,
используйте существующий Python через `py -3.12`, если launcher исправен.
На проверенном ПК оба псевдонима WindowsApps оказались нерабочими, но уже
установлены Python 3.12.10 и 3.14.6. Рабочий вариант без изменения PATH и
системных настроек:

```powershell
Set-Location A:\evolve-ai
$evolvePython = Join-Path $env:LOCALAPPDATA 'Python\pythoncore-3.12-64\python.exe'
& $evolvePython --version
& $evolvePython -m venv --without-pip .venv
& .\.venv\Scripts\python.exe -m evolve --help
& .\.venv\Scripts\python.exe -m evolve doctor
& .\.venv\Scripts\python.exe -m evolve status
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Этот путь зависит от установки Python; на другом ПК укажите фактический
путь к интерпретатору 3.12+. Команда `venv --without-pip` создаёт только
локальную `.venv` без установки пакетов. Активация окружения и изменение
ExecutionPolicy не нужны. Если подходящего Python нет, это предпосылка
запуска: приложение ничего самостоятельно не устанавливает.

Команды `doctor`, `status`, справка и запуск без аргументов завершаются с
кодом **0**. Неизвестная команда, лишние аргументы и ошибочная конфигурация
дают **2**. Проверить код в PowerShell: `$LASTEXITCODE`.

### Что реально работает

- `doctor`: ОС и версия ядра Windows, Python, текущий каталог, источник
  конфигурации. GPU/Vulkan и ресурсы не проверяются на этом этапе.
- `status`: версия 0.0.0, режим, состояние `idle`, отсутствие моделей и API.
  Это состояние основы без очереди задач и работающего агента.
- `--help` и запуск без аргументов: описание доступных команд.
- TOML-конфигурация с проверкой схемы, кодировки и размера.

На этапе 00 пакеты `core`, `models`, `memory`, `tools`, `safety`, `evaluation`,
`observability` содержат только поясняющие docstring. Backend, память,
policy engine, инструменты, оценка и аудит пока **не реализованы**. `mock`
сейчас лишь допустимое имя режима; генерации ответов нет. Все сообщения
выводятся в stdout/stderr; файловых журналов и телеметрии нет.

### Конфигурация

По умолчанию читается `evolve.toml` **в текущем рабочем каталоге**. Если
такого файла нет, используются встроенные настройки `offline`; `doctor`
показывает это явно. Для локальной копии:

```powershell
Copy-Item evolve.toml evolve.local.toml
& .\.venv\Scripts\python.exe -m evolve --config .\evolve.local.toml status
```

Флаг `--config` ставится **перед командой**. Явно указанный отсутствующий
файл — ошибка. Допускается только секция `[evolve]` с параметром
`mode = "offline"` или `mode = "mock"`; пустой файл использует offline.
UTF-8, включая BOM от Windows PowerShell 5.1, поддерживается; максимум
16 КиБ. Неизвестные секции, параметры и режимы отклоняются. Содержимое
неверного файла в ошибку не копируется. Конфигурация не включает сеть,
внешние API, запуск процессов или будущие возможности. Переменные `.env`
не читаются, ключи не нужны.

Обычный Python может создавать `__pycache__` внутри исходников. Для
запуска без записи байткода используйте `python -B -m evolve status`.
Тесты создают временные файлы только в `.test-tmp/`, которая игнорируется
Git; дочерние команды ограничены таймаутом 10 секунд. Отдельный тест
блокирует Python audit events сети, запуска процессов и записи файлов
при реальном выполнении CLI. Это проверка основы, а не будущая песочница
для недоверенного кода.

### История и откат

Владелец опубликовал этап 00 через GitHub Desktop в ветке `main`.
Коммит основы: `13c2ad8558e66fd0ff9c0f03b98458f6489b02dc`
(`feat: complete phase 00 foundation`). Публикация независимо проверена;
результаты и ограничения среды Codex описаны в `docs/PROGRESS.md`.
Для получения истории в новом каталоге:

```powershell
git clone --branch main https://github.com/MrAngryCat/evolve-ai.git A:\evolve-ai-checkout
```

Для отмены уже опубликованного изменения используйте `git revert <commit>`
после проверки нужного коммита; не применяйте force push. Проект не
устанавливает сервисов и драйверов и не меняет системные настройки.
Никакие платные зависимости или API не требуются. Сеть использовалась
разработчиком только для запрошенной публикации в GitHub; CLI работает
офлайн. Упаковка через pip/build в этапе 00 не проверялась и для запуска
не требуется; setuptools указан только как необязательная для такого
запуска зависимость сборки.

## Этап 01: ресурсы компьютера

```powershell
& .\.venv\Scripts\python.exe -m evolve doctor --resources
& .\.venv\Scripts\python.exe -m evolve doctor --resources --json
```

Расширенная диагностика работает офлайн без установки пакетов. Проверяет CPU,
RAM, выделенную VRAM через DXGI, диск проекта и установленный Vulkan.
Неизвестные значения обозначены `null`; успех перечисления Vulkan не означает
совместимость модели или inference. Команды не устанавливают ничего и не
меняют системные настройки. Обычные `doctor` и `status` сохранены.
Описание источников, профилей Idle/Balanced/Research, предположений и ограничений:
[docs/PHASE_01.md](docs/PHASE_01.md). Измеренный снимок:
[docs/HARDWARE_REPORT.json](docs/HARDWARE_REPORT.json).
Этап 02 требует отдельной приёмки.

## Этап 02: ядро и события

```powershell
& .\.venv\Scripts\python.exe -m evolve demo
```

Команда выполняет четыре **имитационные** задачи без LLM, сети, файлов и TTS.
Core управляет Goal/Task/Run, проверяет переходы, формирует историю событий
текущего процесса и поддерживает совместную отмену. История не сохраняется
после выхода. Это не реальное исследование или самоулучшение.
Правила, интерфейс, ограничения и тестирование: [docs/PHASE_02.md](docs/PHASE_02.md).
Этап 03 требует отдельного разрешения.

## The first true autonomy test

Owner: **«Evolve, добавь себе качественный русский синтез речи»**.
Later, after research/executor/security/evaluator components work, Evolve should discover candidate TTS engines, prepare an isolated plugin and tests, compare output and latency, submit a reviewable diff, and—with the owner's approval—activate it. Passing this test proves an end-to-end capability-acquisition workflow, *not* that the base model has retrained itself.
