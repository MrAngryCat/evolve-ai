# Phase 02 - Core and Event System

## Scope, baseline and implementation plan

Owner authorized phase 02 only after acceptance of phases 00/01. Before edits:
working tree clean, branch phase-02-core-events, HEAD/main at
4ad6b2d2eafbdeb88e2dbb593e307b476959b657. GitHub main independently resolved
to the same commit; phase 01 is an ancestor of main (git exit 0).

Plan executed: immutable typed snapshots -> controlled in-memory lifecycle ->
ordered event history -> trusted synthetic executor -> finite demo -> mocked,
offline tests and review. No earlier feature is rewritten. Phase 03 is excluded.

## Files and responsibilities

- core/entities.py: State enum and frozen Goal, Task, Run, Event dataclasses;
  bounded immutable JSON-like payload conversion.
- core/events.py: synchronous EventBus, sequence ordering and subscriptions.
- core/executor.py: Executor Protocol, monotonic Cancellation, synthetic MockExecutor.
- core/orchestrator.py: entity ownership, registration, selection, attempts,
  cancellation, explicit retry and shutdown.
- core/demo.py: exactly four simulated steps with no external operations.
- core/__init__.py exports the public API; CLI adds only `demo`.

## Entities and lifecycle

IDs are unique strings generated as UUIDs; Run has a new ID per actual attempt,
an attempt number and linked Task/Goal IDs. Events use monotonic per-bus sequence
numbers. Clock/ID factories can be supplied for deterministic fixtures. Timestamps
default to timezone-aware UTC. Injected factories are trusted application code.

All public snapshots are frozen; collections are tuples and nested mappings are
read-only copies. Mutating a caller's copy cannot alter registered business state.
There are no public setters or generic transition methods. Internal dictionaries
are process-local; the underscores are encapsulation, not a security sandbox.

| Entity | State rules |
|---|---|
| Task | pending -> running -> completed/failed/cancelled; pending -> cancelled |
| Retry | Explicit retry_task moves a terminal Task to pending and clears its current result/error; its previous Runs stay terminal and unchanged |
| Run | Created running immediately before execution; ends completed/failed/cancelled once. No API reruns an existing Run; MockExecutor also rejects terminal Run inputs |
| Goal | Empty/all pending -> pending; partial progress -> running; all terminal -> failed if any failed, else cancelled if any cancelled, else completed |

Retrying a task may reopen its Goal. A Goal with some completed tasks and pending
tasks remains running. Register all tasks before execution: add_task accepts only
pending Goals and is blocked during an execution. Task selection is insertion
order within the requested Goal; unrelated goals are not executed or cancelled.
No DAG/dependency planner, scheduler or automatic retries are present.

execute_next performs at most one attempt and returns a terminal Run snapshot,
or None when no pending task exists. Reentrant execution is rejected through
terminal event delivery. Calls must be made from one application thread; no
concurrent/thread-safe execution guarantee is made.

## Cancellation and shutdown

cancel_task is idempotent for terminal/already-requested tasks. Pending tasks
become cancelled without inventing a Run. Running tasks receive a monotonic
cancellation request; executor checkpoints and a post-return checkpoint observe
it. If a trusted executor never returns/checks, Core cannot force it to stop.
No code is executed in an external process or sandbox at this phase.

close rejects new work immediately, cancels waiting tasks and requests running
cancellation. core.closed is emitted only after any active attempt is finalized.
Repeated close has no effect. Errors derived from Exception are converted to
failed with the fixed code executor_error; raw messages/tracebacks are not stored.
ExecutionCancelled becomes cancelled. KeyboardInterrupt/SystemExit are finalized
as cancelled and re-raised. Existing custom clocks/handlers/executors are trusted
in-process extensions, not inputs accepted from a model.

## Event contract

History is a tuple of immutable Event objects. Events have kind, UTC timestamp,
source, related IDs and payload; Core emits fixed metadata rather than logging
user descriptions or executor results. Event kinds include goal.created,
task.created, run.started, run.completed/failed/cancelled, task.cancelled,
task.cancel_requested, task.retry_requested, goal.completed/failed/cancelled,
core.close_requested and core.closed.

State updates occur before associated event handlers observe them. Nested event
emissions queue behind the current event so each subscriber sees sequence order.
Subscription lists are snapshotted per delivery. Subscriber Exception failures
increment a counter and do not fail tasks; no raw error is retained and no
recursive error event is emitted. There is a limit of 256 emissions per dispatch
chain, preventing a subscriber's emission loop from growing forever. A handler
that itself hangs is not forcibly interruptible.

Payloads allow finite JSON-like scalars, lists/tuples and mappings; mapping roots
only for event payload and execution results. Limits: 8 nesting levels, 64 items
per container, 1024 nodes per conversion, 4096 characters per string, 256-bit
integers and 80-character keys. NaN/infinite numbers and executable objects are
rejected. Credential-like keys are rejected, but this is not a universal secret
detector: callers must never put secrets into strings or descriptions. Metadata
is bounded printable text/None, never a mutable external object.

History is only for the current process and grows with explicit application
actions; there is no disk log, SQLite, persistence adapter or durable audit claim.
Future storage can serialize the snapshots/events outside the current business
rules; it is not preimplemented here.

## Example and CLI

```python
from evolve.core import Orchestrator, MockExecutor

core = Orchestrator()
goal = core.create_goal('Synthetic example')
task = core.add_task(goal.id, 'Simulated step')
run = core.execute_next(goal.id, MockExecutor())
assert run.status.value == 'completed'
core.close()
```

```powershell
Set-Location A:\evolve-ai
& .\.venv\Scripts\python.exe -m evolve demo
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Demo is explicitly labelled DEMO, with no research, coding, real TTS, LLM or
self-improvement. It registers a TTS-themed goal and four synthetic tasks, then
makes exactly four calls to execute_next. Printed history before shutdown:

1. goal.created
2. task.created (four events)
3. run.started -> run.completed (four attempt pairs)
4. goal.completed; summary Goal: completed

There are 14 printed events; close is then called. MockExecutor supports success,
fail and cancel modes, returns structured demo-only data, and has no file,
network, subprocess, OS-control or language-model tools. Doctor/status retain
their existing behavior; MockExecutor is not a mock language backend.

## Tests, review and publication

tests/test_core.py covers creation, ownership, success/failure, cancellation and
repeated cancellation, retries/attempt identity, immutable payloads and metadata,
invalid transitions, order, independent goals, subscriber errors/reentrancy,
bounded event chains and payload expansion, deferred shutdown and CLI demo.
A Python audit guard forbids file opens, network, subprocesses and registry access
around actual mock execution. It is behavioral regression evidence, not a sandbox.
Original tests for phases 00/01 remain unchanged. Actual commands/results are in
PROGRESS.md, including red regressions before fixes.

Read-only review findings on duplicate goal events, stale cancellation observers,
mutable event metadata and unbounded payload/event chains were addressed. No
models, new dependencies, Windows settings or paid services were introduced.

Work belongs on phase-02-core-events. If Git refuses index writes, open this repo
in GitHub Desktop on that branch, review only stage 02 files, commit
`feat: add phase 02 core and event system`, then Publish branch / Push origin.
Do not force push. Review and phase 03 authorization remain separate decisions.
