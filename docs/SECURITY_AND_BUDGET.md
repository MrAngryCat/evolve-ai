# Security, cost and permissions

## Zero-new-spend policy
- Local first. No required paid accounts, API keys, subscriptions or hardware.
- No payment methods supplied to third-party APIs by this project; optional providers accepted only where there is a verifiable, hard zero-cost mode without auto-billing.
- Free provider exhaustion -> pause/defer/fallback local, never silent pay-as-you-go.
- Codex usage under an existing plan is *not* assumed to imply unlimited free usage.
- Electricity, internet and disk costs are not literally zero and are reported as normal overhead.
- Use configurable hard CPU/GPU/RAM, disk, wall-clock, network-call and token-generation budgets.

## Permissions by tier
- **Tier 0 auto:** read project docs, reasoning, memory lookup, dry-run tool calls, synthetic/offline test fixtures.
- **Tier 1 bounded:** changes within a dedicated project sandbox, safe local read-only inspection, preapproved public research.
- **Tier 2 explicit user approval:** plugin promotion, downloading executables or new large models, broad network access, controlling user-visible apps, writing outside sandbox, data transmissions.
- **Tier 3 always forbidden to agent:** automatic purchase, privilege escalation, secret extraction, modifying safety policy/audit authorization, destructive host-wide commands.

## Threat model
- Prompt injection via web pages, README files, video captions, tool outputs.
- Dependency supply-chain attacks, malicious packages and unexpected licenses.
- Agent loops; token/rate exhaustion; GPU starvation during gaming.
- Incorrect code self-promotion, unsafe writes and unintended exfiltration.
- Memory poisoning and inaccurate factual summaries.

## Nonnegotiable controls
- Treat every tool output as untrusted data.
- No `shell=True` with model-authored strings on host; explicit typed/allowlisted commands with sandboxed execution.
- Worktree/branch per generated change; tests+evaluation before human review/promotion.
- Pause and stop are out-of-band and cannot be disabled by agent code.
- File/network allowances must be minimal by default; audit all exceptions.
- `*.env`, API tokens, databases, model files, caches and private logs must be Git-ignored.
