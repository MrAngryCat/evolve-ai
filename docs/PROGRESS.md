# Canonical progress

- Plan version: 1.0
- Last updated: 2026-11-14
- Current phase: 02 - Core and Event System
- Phase status: READY_FOR_REVIEW
- Architect review: phases 00/01 accepted per owner; phase 02 awaits review
- Last approved phase: 01; phase 02 authorized, phases 03-20 not authorized
- Publication status: phase 01 merged/published; phase 02 changes currently local
- Tested code: see current phase 02 verification below
- Benchmarked local models: none
- Dependencies installed: none; local `.venv` created with `--without-pip`
- GitHub: https://github.com/MrAngryCat/evolve-ai, default branch `main`
- Published foundation commit: `13c2ad8558e66fd0ff9c0f03b98458f6489b02dc` (`feat: complete phase 00 foundation`)
- Final documentation: prepared locally; separate commit/push outcome recorded below

## Phase 02 - 2026-11-14

Preflight: clean phase-02-core-events at 4ad6b2d2eafbdeb88e2dbb593e307b476959b657;
local main and GitHub main confirmed at same commit. Phase 01 ancestor check
exited 0; all diagnostic files present. No existing local changes overwritten.

Implemented frozen Goal/Task/Run/Event snapshots; explicit lifecycle and retries;
finite one-at-a-time Orchestrator; cooperative cancellation and idempotent close;
synchronous ordered event history with safe subscriptions; structured synthetic
executor success/failure/cancellation; four-step demo with 14 printed events.
No persistence, real model, external execution, background thread or scheduler.

Created: evolve/core/entities.py, events.py, executor.py, orchestrator.py, demo.py;
tests/test_core.py; docs/PHASE_02.md.
Modified: evolve/core/__init__.py, evolve/cli.py, README.md, docs/DECISIONS.md
(ADR-0008), docs/PROGRESS.md. Prior 29 tests unchanged.

Review/fixes: reproduced premature core.closed, duplicate goal terminal event
and terminal-Run mock acceptance with failing tests. Corrected deferred shutdown,
aggregate state before cancellation delivery and once-per-transition terminal
events. Read-only reviewer also identified mutable event metadata, exponential
payload copying and unbounded subscriber emission chains; bounded/immutable
validation and regression tests added. Demo is explicitly synthetic.

Security/cost: no new dependencies, installs, models, network calls from Core,
OS tools, credentials, file logs, SQLite or paid services. Only developer read-only
GitHub verification used network. Immutable snapshots are encapsulation, not a
sandbox; only trusted in-process executors/subscribers are supported. Cooperative
cancellation does not interrupt arbitrary code. History is volatile and requires
caller-managed lifetime; dispatch chains and individual payload work are bounded.

Current authoritative scope is this section; phase 01/00 records below describe
their historical implementation/authorization states. Phase 03 remains forbidden.

### Actual phase 02 verification

| Command | Exit | Result |
|---|---:|---|
| `& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core.py -v` before implementation | 1 | Expected missing Orchestrator import (red baseline) |
| Targeted core regressions `-k close_during`, `-k remaining_task`, `-k completed_run_rejected` before fixes | 1 each | Reproduced premature close, duplicate terminal event and terminal Run acceptance |
| `& .\.venv\Scripts\python.exe -m unittest discover -s tests -v` final | 0 | **54 tests pass, 51.687 s** (29 existing + 25 Core) |
| Existing Python 3.14.6 executable: `-B -m unittest discover -s tests -p test_core.py -v` | 0 | 25 Core tests pass, 0.007 s |
| `& .\.venv\Scripts\python.exe -B -m evolve demo` | 0 | Explicit DEMO; four completed synthetic runs, 14 printed events, final completed Goal |
| `git diff --check` | 0 | Tracked changes have no whitespace errors |

No phase 00/01 test files were edited. Run the same full unittest command to
reproduce verification; timings are this run's measurements, not performance goals.

Git publication: `git add -- evolve/core evolve/cli.py tests/test_core.py
docs/PHASE_02.md docs/PROGRESS.md docs/DECISIONS.md README.md` failed exit 128:
`.git/index.lock` Permission denied. No commit/push attempted after the denial;
no bypass. Existing phase-02-core-events branch remains the correct base.
`git diff --exit-code -- tests/test_cli.py tests/test_resources.py evolve/diagnostics
evolve/config.py` exited 0, confirming previous phase files are preserved.
GitHub Desktop: select phase-02-core-events, review the 12 stage files listed
above, commit `feat: add phase 02 core and event system`, Publish branch / Push
origin, then obtain architect/owner review before merge or stage 03 work.

## Phase 01 - 2026-11-13 (historical)

Current scope supersedes old authorization/status statements in the historical
phase 00 report below. Clean baseline: `606b7af`, main tracking origin/main;
previous documentation changes were committed by owner, nothing overwritten.

Implemented: stdlib Windows diagnostics, optional doctor --resources / --json,
portable mocked tests, measured privacy-filtered JSON snapshot and load-profile
descriptions. No model execution/download, dependencies, agent loop, policy/tool
executor, automatic resource control or phase 02 implementation.

Created: evolve/diagnostics/__init__.py, evolve/diagnostics/windows.py,
tests/test_resources.py, docs/PHASE_01.md, docs/HARDWARE_REPORT.json.
Modified: evolve/cli.py, README.md, docs/DECISIONS.md (ADR-0007), docs/PROGRESS.md.

Real measurements: Ryzen 7 7800X3D 8/16 x64; 31.12 GiB OS-visible RAM,
16.46 GiB available, 47% load; RX 6700 XT 11.96 GiB dedicated VRAM plus AMD
integrated graphics; 288.68 GiB disk free; Windows 10.0 build 26200 x64,
Python 3.12.10 64-bit. Vulkan device enumeration works, API 1.4.315,
driverInfo 26.10.1, Vulkan driverVersion 2.0.353. Inference remains untested.
Full bytes/timestamp in HARDWARE_REPORT.json, interpretation in PHASE_01.md.

Limitations: CIM did not provide CPU/Windows driver version; native CPU fallback
succeeded, CPU load and CIM driver remain unknown. DXGI repeats an adapter entry;
not independent VRAM pools. SSD type, bandwidth, free VRAM and model speed unknown.
9B is a promising resource candidate only. 35B exceeds current conservative
RAM-only/full-GPU weights budgets; split offload untested. Planning reserves and
nominal four-bit lower bounds are assumptions, not requirements or benchmarks.

Read-only review identified Vulkan block attribution, unsafe PATH execution and
post-capture output limiting. Fixed: GPU block parser, trusted .exe locations,
streaming 256 KiB combined-output cap with child timeout. Added regression tests.
No third-party code copied; platform documentation sources listed in PHASE_01.md.

Verification commands actually run:

| Command | Exit | Result |
|---|---:|---|
| `& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_resources.py -v` before module existed | 1 | Expected missing-module error (red baseline) |
| Targeted `-k fields_stay` resource test before Vulkan parser fix | 1 | Expected wrong-device attribution reproduced |
| `& .\.venv\Scripts\python.exe -m unittest discover -s tests -v` final | 0 | 29 tests, 52.477 s; original 13 unchanged plus 16 diagnostics tests |
| `& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_resources.py -v` final targeted run | 0 | 16 tests, 0.080 s |
| Existing Python 3.14.6 executable with `-B -m unittest discover -s tests -p test_resources.py -v` | 0 | 16 tests, 0.077 s |
| `& .\.venv\Scripts\python.exe -B -m evolve doctor --resources --json` | 0 | Actual hardware snapshot, sanitized and saved as docs/HARDWARE_REPORT.json |
| Python AST parse of source/tests and saved JSON parse | 0 | Valid syntax and JSON; inference_tested false |
| `git diff --check` | 0 | No whitespace errors in tracked changes |

Real probes are read-only and local. Mocked diagnostic tests check missing Vulkan,
unknown GPU/data, low disk, redacted failures, no network/system-write actions,
privacy, trusted executable selection, output overflow and process timeout.
No performance benchmark, model runtime or system policy enforcement is claimed.
Phase 01 status: READY_FOR_REVIEW with stated CIM/free-VRAM/storage-type limitations;
publication requires owner GitHub Desktop action due environment denial.

Git: `git switch -c phase-01-diagnostics` failed exit 128 (refs lock Permission
denied). No commit/push attempted or claimed; no bypass. In GitHub Desktop create
phase-01-diagnostics carrying changes, review the nine files listed above,
commit `feat: add phase 01 resource diagnostics`, Push origin. Final acceptance
and phase 02 authorization are separate owner/architect decisions.

## Final phase 00 verification - 2026-11-13 (historical)

This section supersedes the historical failed publication attempts below.

- Owner published through GitHub Desktop. GitHub integration independently
  resolved remote `main` to `13c2ad8558e66fd0ff9c0f03b98458f6489b02dc` and
  retrieved this commit with its expected message and 28 added source files.
- Local `main` and `origin/main` resolve to the same full SHA. Before documentation
  edits, `git status --porcelain=v1` was empty and `git diff --exit-code main --`
  exited 0. Thus the tested tracked working copy matches the published commit,
  subject to Git's normal line-ending normalization.
- Published inventory: `.gitignore`, `AGENTS.md`, `README.md`, `pyproject.toml`,
  `evolve.toml`, 11 Python files under `evolve/`, `tests/test_cli.py`, nine files
  under `docs/`, and two under `prompts/` (28 total). Required instructions,
  source, documentation and tests are present in the GitHub commit.
- Tracked-path inspection found no virtual environment, temporary/cache data,
  private config/database/log files, model weights or private-key files. A
  local scan of all 28 text files for private-key headers and common GitHub,
  AWS and API-token patterns found no matches (exit 0). Test-only sentinel
  strings are synthetic; this limited scan is not a universal secret detector.
- Fresh command: `& .\.venv\Scripts\python.exe -m unittest discover -s tests -v`
  passed **all 13 tests in 51.982 seconds, exit 0**. Tests ran against the clean
  published foundation before documentation changes; application code and tests
  remain unchanged.
- Direct `git ls-remote` failed with `Could not resolve host: github.com`, exit
  128. Remote main verification used the authorized GitHub integration instead;
  no claim of a successful fetch or push from this environment.
- Only `README.md` and `docs/PROGRESS.md` are updated for final publication
  bookkeeping. Architecture/ADRs remain unchanged; no dependencies, models,
  system changes or paid services were introduced. Network access was limited
  to repository verification/publication attempts. Phase 01 is not authorized.

### Final documentation commit

`git diff --check` passed (exit 0). `git add -- README.md docs/PROGRESS.md`
failed (exit 128): unable to create `.git/index.lock`, Permission denied.
No commit or push was attempted after that denial; no restriction was bypassed.
The two documentation updates remain local and uncommitted. Use GitHub Desktop: open
`A:\evolve-ai`, select `main`, review only README.md and docs/PROGRESS.md,
commit with `docs: finalize phase 00 publication report`, then Push origin.
Do not include generated files or use force push. This does not invalidate the
independently verified foundation publication above.

## Historical failed publication attempt - 2026-11-13

Scope: publish the existing, preliminarily accepted phase 00 only, to the existing
`MrAngryCat/evolve-ai` repository. No new repository or phase 01 work.

### Actual results

- Local inspection: `git status --short --branch` reports no commits on
  `phase-00-foundation`; `git remote -v` is empty; `git log -1 --oneline`
  exits 128 because the branch has no commits. Known environment restrictions
  on `.git` were not bypassed; no force operations or permission changes.
- The GitHub integration can read repository metadata. Although metadata lists
  the account's repository push permission, this does not establish the
  integration's ability to write repository contents.
- `github.fetch_file` for `.gitignore` returned HTTP 404 with the explicit
  message `This repository is empty.`
- Attempted `github.create_file` for the already reviewed local `.gitignore`
  as a minimal initial commit on the repository's default branch. GitHub
  returned **HTTP 403: `Resource not accessible by integration`**.
- No commit SHA was returned, and no source file was successfully published.
  No existing history was overwritten. No further publication route or
  browser/permission workaround was attempted after this rejection.
- The immediate blocker is the current integration authorization rejecting
  contents writes to this repository. The API response alone does not identify
  whether repository selection, installation scope or contents permission is
  responsible. A permitted write connection must be restored before retrying.

### Source selection and checks

- The complete source candidate inventory contains **28 files**: the 16 files
  created for foundation, the existing project instructions/documentation and
  prompts. Every candidate path was checked against an explicit 28-path
  allowlist before the attempted upload. `.venv`, caches, secrets, model files
  and temporary data were not selected or sent.
- `git check-ignore .venv/Scripts/python.exe .test-tmp/probe .env local.env
  data/memory.db private.log downloaded.gguf evolve.local.toml` exited **0**;
  all eight representative paths are ignored.
- Re-ran `& .\.venv\Scripts\python.exe -m unittest discover -s tests -v`:
  **13 tests passed in 51.885 seconds, exit 0**. No application code or tests
  were changed during this publication task.
- SHA-256 comparisons before/after the run matched for all **14** application,
  test and configuration/build-metadata files; hash-check command exited **0**.
- Publication-to-local content comparison and required-file presence on GitHub
  remain **unverified because publication failed**. No equality or remote test
  claim is made. The previously reported Python 3.14 test run belongs to the
  foundation implementation, not a fresh run in this completion attempt.
- `docs/PROGRESS.md` records this failure locally. README publication wording
  was corrected to make its clone instructions conditional on a future
  successful publication. These documentation changes could not be committed
  or uploaded through the blocked paths.

### Outcome

Published files: **none**. Publication commit: **none**.
Foundation remains implemented and tested locally; publication is blocked.
No protective setting, integration permission, system setting or billing
configuration was changed. No paid dependency was added. Stop here; **phase 01
is not authorized**.

## Phase 00 - Foundation implementation record (historical)

Publication/branch limitations in this older implementation record describe the
earlier attempt; the final verification section above is authoritative today.

### Implemented scope

- Python >=3.12 package, `python -m evolve`, help/default help, `doctor`, `status`.
- `doctor`: Windows kernel version, Python version, working directory and configuration source. GPU/Vulkan explicitly untested.
- `status`: version 0.0.0, mode, idle state, no model or API adapter. No inference, including in mock mode.
- Small strict UTF-8/BOM TOML config, missing-default offline fallback, explicit missing-file errors, schema/size/parser-limit validation with redacted Russian errors.
- Empty documented packages for core/models/memory/tools/safety/evaluation/observability.
- Source-checkout execution with no pip/runtime dependencies. Pyproject build metadata is present; packaging was not tested or required.
- Standard-library offline tests, ignored local/private/generated files, Windows PowerShell instructions and rollback guidance.

### Created files (16)

```text
.gitignore
pyproject.toml
evolve.toml
evolve/__init__.py
evolve/__main__.py
evolve/cli.py
evolve/config.py
evolve/core/__init__.py
evolve/models/__init__.py
evolve/memory/__init__.py
evolve/tools/__init__.py
evolve/safety/__init__.py
evolve/evaluation/__init__.py
evolve/observability/__init__.py
tests/test_cli.py
docs/PHASE_00_PLAN.md
```

Modified existing files: `README.md`, `docs/DECISIONS.md` (ADR-0006 implementation choices), `docs/PROGRESS.md`.
Existing AGENTS, charter, target architecture, roadmap, model/security/third-party docs and prompts remain unchanged.
`.venv`, bytecode and test scratch files are local generated files, not published source.

### Commands actually run and results

For the commands below, `$evolvePython312` was the already installed
`$env:LOCALAPPDATA\Python\pythoncore-3.12-64\python.exe`; `$evolvePython314`
was the corresponding `pythoncore-3.14-64\python.exe`.

| Actual command | Exit | Result |
|---|---:|---|
| `python --version`, `py --list-paths` | shell 1 | WindowsApps aliases could not execute; no system changes made |
| `& $evolvePython312 --version` | 0 | Python 3.12.10 |
| `& $evolvePython314 --version` | 0 | Python 3.14.6 |
| `& $evolvePython312 -B -m unittest discover -s tests -v` before implementation | 1 | 13 tests, 31 expected failure cases because package was absent |
| Same suite after first implementation | 1 | 2 doctor guard failures: platform.uname indirectly called socket.gethostname |
| Same suite after direct Windows-version fix | 0 | 13 tests pass |
| `& $evolvePython314 -B -m unittest discover -s tests -v` | 0 | 13 tests pass |
| `& $evolvePython312 -m venv --without-pip .venv` | 0 | Local environment created; no pip or downloads |
| `& .\.venv\Scripts\python.exe -m evolve --help` | 0 | Usage and available commands |
| `& .\.venv\Scripts\python.exe -m evolve doctor` | 0 | Windows kernel 10.0 build 26200, Python 3.12.10, cwd/config; GPU not checked |
| `& .\.venv\Scripts\python.exe -m evolve status` | 0 | offline, idle, no models/APIs; future functions explicitly absent |
| `& .\.venv\Scripts\python.exe -m evolve unknown` | 2 | Expected command rejection |
| `& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_cli.py -k invalid_config -v` after adding reviewer regressions | 1 | Expected failure for nested arrays and oversized integer in otherwise small TOML |
| **Final:** `& .\.venv\Scripts\python.exe -m unittest discover -s tests -v` | **0** | **13 tests pass, 8.871 s** |
| **Final:** `& $evolvePython314 -B -m unittest discover -s tests -v` | **0** | **13 tests pass, 8.895 s** |
| Python AST parse of all application/test `.py` files and TOML metadata check | 0 | 12 Python files parse; zero runtime dependencies |
| `git --version` | 0 | Git 2.55.0.windows.2 |
| `git init -b phase-00-foundation` | 0 | Initialized new repository; no existing history overwritten |
| `git remote add origin https://github.com/MrAngryCat/evolve-ai.git` | failed; individual exit not captured | `.git/config` permission denied |
| `git -c credential.interactive=false ls-remote origin` | 128 | Git helper failed under environment restrictions; not a successful network/push check |
| `git check-ignore .venv/Scripts/python.exe .test-tmp/probe .env local.env data/memory.db private.log downloaded.gguf evolve.local.toml` | 0 | All eight representative paths ignored |

The 13 tests contain multiple subcases. They execute actual CLI processes with
timeouts, cover defaults and explicit paths (including spaces/Cyrillic), config
errors/redaction, help/invalid commands and mock-mode honesty. A guarded child
process installs a Python audit hook before package import and fails on network,
subprocess or file-write operations; commands pass with bytecode disabled.
Temporary test files stay within the repository's ignored `.test-tmp/`.
This is behavioral evidence for this foundation, not a sandbox guarantee for
future untrusted code, and no OS firewall isolation was installed.

### Review and fixes

A separate read-only code review found no critical issues and one important
parser error-boundary defect: TOML resource-limit exceptions escaped as raw
ValueError/RecursionError. Real CLI regression cases were added and observed
failing before the fix; errors are now redacted with exit 2, without raising
interpreter limits. Both full final suites passed after the fix. No deferred
minor findings or other unresolved review defects were reported.

Review also confirmed that build packaging is outside this source-run deliverable,
audit guards are tests rather than a sandbox, mock mode is a label, and later
hardware/memory/model/tool/budget functionality is correctly deferred. Git and
progress publication are completion bookkeeping, not an extra agent capability.

### Security, permissions, spending and network

- No model/llama.cpp, dependency, driver or executable downloaded; no third-party code copied.
- No elevation, Windows/PATH/firewall/ExecutionPolicy changes, microphone/screen access by the application, telemetry, background service or loop.
- No secret handling, `.env` loading, external API adapter, paid service, key, billing or mandatory purchase. Existing development tools and ordinary computer overhead still apply.
- Runtime only reads the selected config and reports local state; status does not claim working safety enforcement or persistent/audit capabilities.
- Owner separately authorized browser creation of the public GitHub repository and source publication. These developer publication operations use network access; the application/tests do not require it. No personal folders or secrets are imported.
- GitHub import was attempted through the connected GitHub API because local Git metadata/network helper operations are restricted, but rejected with HTTP 403. README gives a conditional fresh-clone path for use after successful publication. No force push or host restriction bypass.

### Remaining limitations and next gate

- Standard `python`/`py` aliases on this PC remain broken; `.venv\Scripts\python.exe` and explicit existing interpreters work. See README; no system repair attempted.
- The current local checkout has an initialized but uncommitted Git repository; a fresh clone for history is possible only after successful publication.
- `rg` and `gh` are unavailable; neither is a runtime dependency.
- Python packaging/install is untested. Source execution and offline tests are verified.
- GPU/Vulkan, CPU/RAM/disk resource diagnosis, model compatibility and performance remain unverified; they belong to later approved work.
- No backend, persistent memory, tool registry, executor, policy engine, evaluator, audit journal or autonomous loop exists yet.
- The architect has preliminarily accepted stage 00 according to the owner; publication remains blocked. **Do not start phase 01 without approval.** Proposed next phase only: environment/resource diagnosis per `docs/ROADMAP.md`.

### Short architect handoff

The deterministic offline foundation is implemented and reproducibly tested.
The only implementation ADR is ADR-0006; target architecture and phase boundaries
are unchanged. Two Windows/config robustness issues were reproduced and fixed.
The execution environment limits local Git writes; GitHub source import is handled
separately. Please assess phase 00 against the actual tests and scope above; no
model availability, autonomy, persistence or hardware performance is claimed.
