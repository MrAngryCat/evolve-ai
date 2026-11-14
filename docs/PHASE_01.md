# Phase 01 - Environment and hardware diagnostics

## Implementation plan and scope

1. Preserve clean baseline main at `606b7af` (owner committed phase 00 docs).
2. Add isolated stdlib diagnostics behind `doctor --resources`; JSON is pure JSON,
   ordinary doctor/status keep their foundation behavior.
3. Probe RAM via GlobalMemoryStatusEx, GPU dedicated VRAM via DXGI SIZE_T,
   local projected CIM for CPU/driver/OS; native topology and read-only hardware
   registry for CPU fallback. Inspect project-volume capacity only, never files.
4. Run existing trusted vulkaninfo only, with timeout/output cap; allowlist report
   fields. Report unknown/partial results without raw process errors or IDs.
5. Test mocked success/failure/privacy/no actions, retain original 13 tests,
   record real measurements, update progress; stop before phase 02.

No new dependency, model, inference adapter, executor or agent is implemented.

## Run on Windows

```powershell
Set-Location A:\evolve-ai
& .\.venv\Scripts\python.exe -m evolve doctor --resources
& .\.venv\Scripts\python.exe -m evolve doctor --resources --json
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Both diagnostic forms print the same structured fields; the first adds a Russian
explanation. Bytes are exact byte counts; `null`/empty fields mean unknown. The
resource report excludes config paths, username, hostname, serials, adapter IDs
and raw command output. It reads existing config but never prints its contents.
Default commands still report project paths as specified in phase 00; use the
resources report for sharing. No automatic file export is performed by the CLI.
The dated sample in HARDWARE_REPORT.json was saved explicitly during development.

The project disk is the volume containing the installed source package, not a
scan of the current user's files. SSD/HDD type and speed are not verified.
The report is a point-in-time observation and does not reserve resources.

## Probe boundaries

- Two fixed subprocess invocations at most: system PowerShell with a static local
  CIM projection and installed vulkaninfo.exe --summary. shell=False, stdin closed,
  hidden window, ten-second child timeout, combined output capped at 256 KiB
  while reading. Raw stderr is never published.
- vulkaninfo discovery executes only .exe under Windows System32 or C:\VulkanSDK;
  CWD/project scripts and arbitrary PATH locations are not executed. Other installs
  may be present but remain unverified. No SDK installation is attempted.
- Read-only registry access is limited to the CPU hardware description; no writes.
- CIM can be unavailable in a restricted environment. Driver version remains null
  rather than using inaccurate WMI AdapterRAM or claiming CPU load measurements.
- DXGI enumerates adapter entries, which can duplicate a physical GPU. VRAM is
  never summed across entries or combined with shared RAM. Free VRAM is unknown.
- Vulkan states: `working` means successful device enumeration only;
  `detected_unverified` means loader/tool without validated devices;
  `not_detected` means neither allowed tool nor loader found; `error` means probe
  failed. None establishes llama.cpp/model compatibility.
- Installed drivers/tools are trusted local software; these probes are not a
  sandbox for arbitrary executables. Tests with mocked probes run without hardware.

## Measured snapshot (2026-11-13)

See exact timestamp and byte counts in HARDWARE_REPORT.json.

| Resource | Observation |
|---|---|
| CPU | AMD Ryzen 7 7800X3D, 8 physical / 16 logical, x64 |
| CPU load | Unknown; no stress or CPU load sample fabricated |
| RAM | 31.12 GiB OS-visible; 16.46 GiB available; 14.66 GiB used, 47% |
| GPU | RX 6700 XT, 11.96 GiB DXGI dedicated VRAM; integrated AMD Graphics 0.47 GiB |
| DXGI entries | Three entries, including repeated RX 6700 XT; not three independent GPU memory pools |
| Driver | CIM version unavailable; Vulkan driverInfo 26.10.1, driverVersion 2.0.353 |
| Vulkan | Loader and trusted installed tool found, device enumeration successful; both API 1.4.315 |
| Project disk | 288.68 GiB free of 1200 GiB; storage medium/performance unverified |
| OS/Python | Windows kernel 10.0 build 26200, x64; Python 3.12.10 64-bit |

Hardware nameplate 32 GB and reported 31.12 GiB differ because these are different
measures and OS-visible capacity can exclude reserved memory. DDR generation,
memory bandwidth, free VRAM and inference speed were not measured.

## Preliminary model planning - assumptions, not benchmarks

Planning reserves (not enforced): 4 GiB of currently available RAM, 2 GiB of total
dedicated VRAM, and 20 GiB free disk. These are conservative illustrative margins,
not measured application requirements or guarantees. At this snapshot the budgets
are about 12.46 GiB RAM, 9.96 GiB VRAM and 268.68 GiB disk.

The report illustrates a lower bound of nominal parameter count * 4 bits / 8:
9B = 4.5 GB (~4.19 GiB), 35B = 17.5 GB (~16.30 GiB). Real GGUF files differ because
of tensor precision, metadata, quantization and architecture; runtime, KV/context
and scratch memory are additional. A3B active parameters do not eliminate the
need to store other MoE weights. Booleans mean weights-only arithmetic, never
permission to download or a claim that a model will load.

- 9B: promising resource candidate, but actual Qwen hybrid Vulkan support,
  quantization, context/runtime overhead and speed require later tests.
- 35B: exceeds this snapshot's conservative RAM-only and full-GPU budgets even
  before overhead. Split CPU/GPU offload might change feasibility but is untested;
  freeing RAM may help, and performance cannot be inferred. Keep experimental.
- Other GGUF: apply the same measured budgets to the exact file, architecture,
  context and runtime; no format-wide compatibility claim.

## Future load profiles - descriptions only

| Profile | Intended behavior | Still requires measurement |
|---|---|---|
| Idle | No queued compute; unloaded inference where practical | Idle draw and wake latency |
| Balanced | Bounded background work, leave room for desktop/games | Interactive latency and RAM/VRAM peaks |
| Research | Prioritize finite local analysis with explicit owner budgets | Sustained throughput and thermal/game impact |

There are no automatic resource controls or invented performance figures.

## Git and rollback

Git branch creation was denied (exit 128, refs lock permission). Changes remain
local; no commit/push claimed or restriction bypassed. In GitHub Desktop choose
Create branch `phase-01-diagnostics`, carry these changes, review only the nine
listed stage files, commit `feat: add phase 01 resource diagnostics`, Push origin.
After review, rollback can revert that commit; no service or system install needs
to be undone. Final tests/results and file list are in PROGRESS.md.

## API references (documentation only; no code copied)

- https://learn.microsoft.com/en-us/windows/win32/api/dxgi/ns-dxgi-dxgi_adapter_desc1
- https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex
- https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getlogicalprocessorinformation

The existing Microsoft platform APIs are invoked directly; no third-party source
or dependency was imported. Stage 02 is not authorized.
