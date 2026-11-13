# Target architecture — evolve as one system

```
Owner <-> UI/CLI <-> Orchestrator (goal + task + workflow)
                        |        |            |
                        |        |            +--> Policy / budget / approval gate (deterministic)
                        |        +--> Shared state store (SQLite: goals/tasks/events/artifacts/memory)
                        +--> Model router -> Local model adapter(s) -> llama.cpp Vulkan / CPU
                        |                     \-> Optional free-tier adapter [disabled by default]
                        +--> Tool registry -> Browser / Files / Coding Sandbox / Media / TTS / STT / Desktop
                        +--> Evaluator -> unit tests, task metrics, git diff, human promotion
                        +--> Audit + observability + pause/stop and recovery
```

## Logical interfaces (provisional; no implementation required in phase 00)
- `ModelBackend`: load/status, generate(prompt, context, budget), capability metadata, cancel.
- `GoalStore`: durable goals, task graph, priorities, task state and checkpoints.
- `MemoryStore`: append observations, facts and citations; retrieval filtered by relevance and provenance; deliberate forgetting/expiry as needed.
- `PolicyEngine`: evaluates declared tool actions and resource spending; never delegates authorization to the model itself.
- `ToolRegistry`: documented tool schemas, allowlists, resource constraints and explicit return values.
- `Executor`: executes in an isolated sandbox; timeouts, disk, CPU/GPU and network caps, no arbitrary host operations.
- `Evaluator`: unit/integration tests, benchmark regression, change confidence and rollback.
- `PluginManager`: proposed/staged/verified/enabled states; never self-enables privileged plugins.
- `RunJournal`: immutable-ish append-only audit of goal/task/action/decision/test/artifact events, redacting secrets.

## State model
- One external durable state store shared between models, not a shared KV cache nor merged weights.
- All significant agent actions have a task ID/run ID, timestamps, backend used and evidence links.
- Important changes are recoverable from Git/checkpoints; no silent destructive migrations.
- User-facing persona/voice is configuration + memory, never claimed to be independent consciousness.

## Execution modes
1. `offline`: no model or network; smoke test/mock backend; always available.
2. `local-small`: 9B candidate, default where compatible.
3. `local-large`: experimental 35B A3B or successor only if resource preflight passes; stop or defer if not viable.
4. `optional-free-cloud`: not part of core runtime; explicit opt-in with rate/quota ceilings and zero-billing path.

## Privacy posture
- Store only the requested project context; redact secrets in logs.
- User-specific data, browsing and screen recording off unless explicitly enabled.
- UI displays active model, tool permissions, CPU/GPU/RAM load, task source and pending approvals.
