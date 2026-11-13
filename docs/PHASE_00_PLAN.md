# Phase 00 implementation plan

Spec: `prompts/PHASE_00_CODEX.md`, `docs/ROADMAP.md` phase 00 and the owner's execution request.

The approved architecture already specifies Python, an offline CLI and empty future packages. Implement directly in this new project; there is no existing Git history or application to isolate. No dependency installation, model backend, database, executor, agent loop or hardware benchmark belongs to this phase.

## Deliverable and interfaces

- `evolve/__main__.py` delegates to `evolve.cli.main(argv=None) -> int`.
- `evolve/config.py`: immutable `Config(mode, source)` and `load_config(path=None)`, with a dedicated `ConfigError`. Default `evolve.toml` in the working directory; missing default uses offline built-ins. An explicitly requested missing file is an error. Only `[evolve] mode = "offline"` or `"mock"` is accepted. Neither mode implements inference.
- `evolve/cli.py`: argparse help, doctor and status. No command shows help. Unknown command/config error exits 2. Successful commands exit 0. Doctor reports OS, Python, cwd and config source; status reports version, mode, idle and unimplemented capabilities honestly. Output goes to stdout/stderr only.
- `evolve/{core,models,memory,tools,safety,evaluation,observability}/__init__.py`: documentation only.
- `pyproject.toml`: Python >=3.12, no runtime dependencies; run directly from checkout without packaging tools or pip.

## Steps

- [x] Write unittest acceptance tests; run against the absent package and record expected failures.
- [x] Implement only CLI/config and package skeleton; run the full suite.
- [x] Document PowerShell setup, alias fallback, config behavior, exit codes and rollback. Update progress and implementation decisions.
- [ ] Verify on existing Python 3.12 and 3.14; inspect diff and ignored files; initialize Git, commit and publish to the owner-requested GitHub repository.

## Review focus

Tests must cover missing/invalid/unknown/oversized/non-UTF8 config without leaking its contents; invalid commands and help even with broken config; cwd independence through explicit config paths including Cyrillic/spaces; no network, subprocess execution or file writes by commands (Python bytecode disabled in the guard process); no false model/API availability, including mock mode.

The tests use temporary directories inside `.test-tmp/`, and bound CLI subprocesses with timeouts. This guards foundation behavior, not a sandbox for future model-authored code. No file audit log is implemented; observability is reserved for a future phase.

## Execution rulings

- The owner requested GitHub creation/publication during execution. Created public `MrAngryCat/evolve-ai` with the selected visibility. No personal files, credentials or generated environment are part of publication.
- Local Git initialization succeeded, but subsequent `.git/config` writes were denied by the environment and Git's network helper also failed. Publish through the connected GitHub API; leave the local history limitation explicit instead of claiming a successful push. A fresh clone restores normal local Git history outside this execution restriction.
- A read-only reviewer found parser resource-limit exceptions. Added both real CLI regressions, observed failure, and map ValueError/RecursionError to redacted config errors without raising interpreter limits. No other review findings remain. Deferred future features match the phase boundary; build packaging remains untested.
