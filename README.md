# CallGate

A local voice-risk advisory prototype for requests to move money into a "safe account".

**Current boundary:** CallGate transcribes test speech and displays risk evidence and advice. Real human identity enrollment, a trusted confirmation channel, receipt key lifecycle/storage, and enforcement over real tools are not implemented. The microphone demo cannot block a bank transfer or control a phone call.

## Try the current prototype

Follow [本机运行与检查](START_HERE.md) for the existing environment, or [setup and API guide](docs/V2_PHASE1.md) for installation. With dependencies installed, run:

```powershell
python scripts/start_demo.py
```

Open `http://127.0.0.1:8765/`, click Start, and allow microphone access. Streaming transcription requires an AssemblyAI key in the local `.env` and an internet connection. Use synthetic English speech:

1. "Move your savings into the secure holding wallet." → `CHALLENGED`: verify before acting.
2. "Do not tell anyone." → `COOLING_OFF`: pause and verify independently.

These are expected baseline behaviors, not proof of scam detection accuracy. Recognition errors can change the result. Offline checks are available through `Check-CallGate.ps1` without a key or network access.

## What runs today

`Audio → AssemblyAI streaming transcript → English rule events → conversation state → score timeline → advisory Guardian`

- Events reference transcript segments and revisions. Corrections replace current evidence.
- Scores are heuristic reference values, not fraud probabilities or verified identities.
- The four implemented audio states are `UNVERIFIED`, `CHALLENGED`, `COOLING_OFF`, and `BLOCKED`. All provide advice; `BLOCKED` means a warning against sharing sensitive information, not an external action block.
- NetworkX projects current evidence. Separate test components provide Ed25519 confirmation/receipt signatures and a simulated gate with SQLite replay protection. They are not connected to a trusted human confirmation flow in the microphone demo.

## Reuse and project contribution

AssemblyAI supplies streaming transcription; Silero and Pipecat integrations provide optional voice processing components; NetworkX, cryptography and SQLite supply graph, signature and persistence primitives. CallGate adds revision-aware evidence handling, cross-turn action/secrecy rules, advisory policy, and tests of scoped credentials and replay rejection.

This is an integration prototype. Comparative superiority over other projects has not been established. See the [source comparison and reuse notes](docs/V2_RESEARCH.md) for research context.

## Evidence and next milestone

The [local report](scambench/LOCAL_RESULTS.md) records regression tests and 25 same-author synthetic development cases. These do not estimate real-world accuracy. The private evaluation structure exists; an independently authored evaluation dataset is still needed. Engine timings and scripted audio timestamps do not establish live speech-to-alert latency.

Next: connect one safe-account scenario to a pre-enrolled reviewer and a demo-only protected action. Show valid confirmation, forged confirmation, expiry, replay and unavailable confirmation outcomes before expanding scope. Measure live alert latency and actual service cost for that path.

## Reference material

- [Run and API details](docs/V2_PHASE1.md)
- [Local results](scambench/LOCAL_RESULTS.md)
- [Build history and disclosure](BUILD_LOG.md)

The remaining documents in `docs/`, including architecture, threat model, product strategy and pitch plans, are design/reference material. Their future capabilities are not implementation claims. Original research is preserved at commit `16c469ae78f22f06df757595b8b36edd9359086e`.

## License

[MIT](LICENSE). Reused libraries and models retain their respective licenses and attribution.
