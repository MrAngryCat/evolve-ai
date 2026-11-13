# Canonical progress

- Plan version: 1.0
- Last updated: 2026-11-13
- Current phase: 00 - Repo foundation
- Phase status: READY_FOR_REVIEW
- Architect review: preliminary acceptance of phase 00 reported by the owner; publication remains incomplete
- Last approved phase: no authorization for phase 01
- Publication status: BLOCKED (GitHub integration rejected write access)
- Tested code: phase 00 CLI/configuration on existing Windows Python 3.12.10 and 3.14.6
- Benchmarked local models: none
- Dependencies installed: none; local `.venv` created with `--without-pip`
- GitHub: public https://github.com/MrAngryCat/evolve-ai exists; confirmed empty during the completion attempt below
- Local Git limitation: initialization succeeded, subsequent `.git/config` write denied by execution environment; no local commits or successful push claimed

## Publication completion attempt - 2026-11-13

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

## Phase 00 - Foundation

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
