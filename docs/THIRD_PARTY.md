# Third-party research and license register

Nothing below is yet imported into Evolve AI. Never imply these implementations are ready to run on RX 6700 XT without evaluation.

| Candidate | Project link | Value | Required due diligence |
|---|---|---|---|
| llama.cpp | https://github.com/ggml-org/llama.cpp | Local inference, Vulkan, CPU offload | Check current license, binary origin, GGUF and Vulkan feature support |
| Qwen3.5-9B | https://huggingface.co/Qwen/Qwen3.5-9B | Small model candidate | Official license and GGUF conversion provenance |
| Qwen3.5-35B-A3B | https://huggingface.co/Qwen/Qwen3.5-35B-A3B | Large MoE candidate | Current Windows Vulkan support, RAM/SSD budget |
| Qwen3.6 | https://github.com/AlibabaCloud-Official/Qwen3.6 | Alternative model family | Benchmark relative to 3.5 and check license of actual checkpoint |
| Neuro (KimJammer) | https://github.com/kimjammer/Neuro | Prompter, modular voice, memory ideas | Verify LICENSE on actual commit; preserve MIT attribution where applicable |
| Neuro_sama fork | https://github.com/nops1ed/Neuro_sama | Community experimentation | Inspect fork license and modification delta |
| Open-LLM-VTuber | https://github.com/Open-LLM-VTuber/Open-LLM-VTuber | Real-time voice/visuals ideas | Separate library/model asset licenses |
| Piper | https://github.com/OHF-Voice/piper1-gpl | Local speech synthesis | GPL obligations and individual voice model licenses |
| whisper.cpp | https://github.com/ggml-org/whisper.cpp | Local STT | License and RAM/VRAM benchmarks |
| Playwright | https://playwright.dev/ | Controlled browser tasks | Browser binaries and site rules |

## Import checklist
1. Pin source URL, commit/tag, copyright and license in this register.
2. Check transitive dependencies and model/voice asset licenses.
3. Verify architecture/Windows + AMD compatibility; provide sandboxed test.
4. Avoid wholesale copy/paste; prefer adapters unless license/maintenance justify porting.
5. Document local modifications and update notices when required.
