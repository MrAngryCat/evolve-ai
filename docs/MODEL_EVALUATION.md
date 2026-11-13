# Local model test protocol (not benchmark results)

## Hardware assumptions to verify
- Ryzen 7 7800X3D, Radeon RX 6700 XT (12GB VRAM), 32GB RAM.
- Actual Windows version, driver, Vulkan, disk and available memory under Windows are unknown.

## Candidates, not commitments
- **Fast:** Qwen3.5-9B (official checkpoint; GGUF quantized conversion) or better small model shown by local tests.
- **Large:** Qwen3.5-35B-A3B or newer Qwen3.6-35B-A3B (verify licenses, GGUF validity, hybrid/SSM Vulkan backend and quality); can remain deferred.
- **Engine:** maintained llama.cpp build with Vulkan support; verify exact build and hashes.
- Open-source local project must run without cloud; 35B is not guaranteed to fit comfortably or perform well.

## Evaluation matrix per candidate
- Exact model repo, revision, SHA256, quantization, model license, llama.cpp build and flags.
- End-to-end validation: coherent response (not corrupted), reliable tool-call format, long context sanity, stream cancel.
- RAM / VRAM peak, first-token latency, generated tokens/s, prompt processing tokens/s at 4K and 8K context.
- Windows gaming impact with optional reduced-resource mode; note ambient load.
- Representative coding tasks: compile a 25-line module, fix deterministic bug, edit API using only docs, produce passing tests.
- Shared memory continuity: same task switches models after one model unloaded and continues from retrieved external DB notes.
- At least three repeated runs; record median and run-to-run variability.
- Failed benchmarks stay failed; never invent numbers or label as 'supported'.

## Vulkan warning
Qwen3.5 hybrid models have historically triggered incompatible DeltaNet/SSM operations in Vulkan builds of llama.cpp. A closed GitHub issue (#19957) records earlier garbage-output/driver errors in a setup; closed does not guarantee fixed on this Radeon. Test real output and crash resistance prior to enabling large model.

## Citations / primary sources
- https://github.com/ggml-org/llama.cpp/blob/master/docs/install.md
- https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md
- https://github.com/ggml-org/llama.cpp/issues/19957
- https://huggingface.co/Qwen/Qwen3.5-9B
- https://github.com/AlibabaCloud-Official/Qwen3.6
