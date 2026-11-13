# Project Charter — Evolve AI

## Vision
Create a private, local-first AI software agent that can acquire new software capabilities via research, planning, coding, testing, comparison and supervised promotion of its own plugins. It may work on long-lived goals and resume after crashes/restarts, while remaining auditable, budget-bound and user-controlled.

## Demonstration scenarios (ordered)
1. `evolve status`: show version, configuration, task state, budgets and backend availability.
2. Shared-memory switch: a task begun with Model A is continued by Model B using the same persisted, retrieved factual context and task status.
3. Autonomous mini-cycle: agent completes a bounded mocked research/coding exercise, logs results and can pause/resume.
4. Capability acquisition: 'Добавь себе русский синтез речи' produces a tested, reviewable TTS plugin without privileged system modification.
5. Advanced later: browser research, documentation/video analysis, voice interface and supervised desktop control.

## Explicitly out of scope initially
- AGI, consciousness and guarantees of unbounded self-improvement.
- Self-training/fine-tuning foundation model weights; may become a future research track with evaluation safeguards.
- Unrestricted control of a personal Windows desktop.
- 24/7 unbounded GPU workloads or guaranteed throughput for 35B model.
- Browser automation of consumer AI chat sites to bypass API fees.
- Paid services, cryptocurrency mining, uncontrolled downloads or system-wide installs.

## Success measures
- Phase-by-phase reproducible tests, audited actions, clear user-facing status and stop mechanisms.
- Testable memory continuity when switching model adapters; maintain source provenance and distinguish facts from hypotheses.
- Task outcomes measured by tests and task-specific benchmarks, not subjective self-scores.
- Zero mandatory *new* subscriptions/API charges/hardware purchases; note normal electrical and Internet use still exist.

## Canonical language
User interaction and docs may be Russian. Identifiers and code should use concise English names. User-facing errors must be understandable in Russian.
