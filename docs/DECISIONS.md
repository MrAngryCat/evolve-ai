# Architecture Decision Log (ADRs)

## ADR-0001 — One system, many model backends (accepted)
Evolve has one task state, identity settings and external memory. Small/large models are replaceable compute backends rather than separate personalities. They are not assumed to load simultaneously.

## ADR-0002 — Local-first, no mandatory new spend (accepted)
Core must work offline with local inference/mock and no paid APIs. Free cloud services remain optional and disabled until expressly enabled.

## ADR-0003 — Supervised self-modification (accepted)
The agent may propose/code/test plugin updates in sandbox. Promotion, security changes and host-level access require owner approval.

## ADR-0004 — Python and SQLite (provisional)
Use Python stdlib and SQLite for initial deterministic skeleton and memory. Review performance when real benchmarks become available.

## ADR-0005 — Vulkan/llama.cpp primary inference experiment (provisional)
Test on actual Windows + AMD hardware; do not commit to 35B support without proof. Qwen3.6 is an alternative under evaluation.

## ADR-0006 - Phase 00 implementation choices (2026-11-13)

Context: the owner requested the approved foundation only; no application or
Git repository existed. These choices implement that scope without changing
the target architecture or approving a later phase.

Options: source checkout versus mandatory package installation; stdlib
`argparse`/`tomllib`/`unittest` versus downloaded CLI/config/test libraries.

Decision: Python >=3.12, flat `evolve/` package, source-checkout execution,
stdlib runtime/tests and no required pip installation. Read a small, strict
local TOML config; absent default means offline, explicit missing path means
error. Modes are labels only until backends are approved. Future subsystem
packages contain documentation only, including observability.

Consequences: no model, network client, task store, tool execution, policy
engine or audit log exists yet. Status reports these absences. Doctor uses
`sys.getwindowsversion()` directly on Windows, avoiding hostname lookups and
the broader probing in `platform.uname()`. Test audit hooks validate CLI
behavior but are not a security boundary for untrusted code. Packaging is
metadata only for now; setuptools is a build-time dependency, not a source
run/test dependency. Initial work stays on `phase-00-foundation` for review.
Phase 01 remains unauthorized.

## ADR-0007 - Phase 01 read-only diagnostics (2026-11-13)

Owner authorized phase 01 only. Use stdlib, native Windows APIs and a fixed local
CIM property projection, with native CPU fallback. DXGI SIZE_T gives dedicated
VRAM without WMI AdapterRAM's 32-bit truncation. No summed shared RAM/VRAM.
Optional installed Vulkan summary is restricted to system/VulkanSDK executables;
no arbitrary shell, command string from users/models, or tool registry is added.
Subprocesses have timeout and streaming output cap; published fields omit IDs,
paths and raw errors. Collection is opt-in behind doctor --resources; JSON is
versioned, unknown values are explicit, CPU/GPU profiling and controls deferred.
Model-fit arithmetic is illustrative weights-only, not a compatibility benchmark.
This leaves target architecture intact and does not authorize phase 02.

## Change format
Each new ADR: id, date, context, options considered, decision, consequences and owner approval if architecture changes.
