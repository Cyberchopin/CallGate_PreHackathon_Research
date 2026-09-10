# CallGate

A local voice-risk advisory prototype for requests to move money into a "safe account".

**Current boundary:** CallGate transcribes test speech and displays risk evidence and advice. A separate local text-replay demo now supports explicit reviewer confirmation and a simulated action. Real human identity enrollment, remote trusted reviewer transport, receipt key lifecycle/storage, and enforcement over real tools are not implemented. The microphone demo cannot block a bank transfer or control a phone call.

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

## Try the local confirmation path

Run `./Start-Review-Demo.ps1` in PowerShell, or `python -m scripts.start_review_demo` in the complete environment. The launcher prints two private entry links: participant on port 8766 and reviewer on 8767. Open each complete link, including its fragment, in the appropriate browser window. Nothing is installed and no cloud API is called.

1. Participant: analyze the prefilled safe-account sentence, then submit the fictional amount and destination.
2. Reviewer: read the current request, check the exact amount and destination, then explicitly approve or deny.
3. Participant: refresh the result. Approval permits one simulated action only. New transcript content invalidates pending confirmation; secrecy/credential states prevent a new request.

Each role has a different bearer capability. The reviewer private key is generated only inside the reviewer process; the participant backend receives its public key. The reviewer checks the displayed operation against its signed digest before signing. Both processes and the host are trusted; the participant backend still owns the policy and issuer key. Possession of the reviewer link is the demo's authorization mechanism, not proof of human identity. Do not give that link to the participant.

Keys and pending state are ephemeral; restart invalidates old entries. This launcher uses an in-memory replay gate and one session per startup. It is a text-replay demo, not yet connected to the microphone stream. Tests exercise real loopback HTTP across both processes, including repeat approval rejection and reviewer unavailability.

## Reuse and project contribution

AssemblyAI supplies streaming transcription; Silero and Pipecat integrations provide optional voice processing components; NetworkX, cryptography and SQLite supply graph, signature and persistence primitives. CallGate adds revision-aware evidence handling, cross-turn action/secrecy rules, advisory policy, and tests of scoped credentials and replay rejection.

This is an integration prototype. Comparative superiority over other projects has not been established. See the [source comparison and reuse notes](docs/V2_RESEARCH.md) for research context.

## Evidence and next milestone

The [local report](scambench/LOCAL_RESULTS.md) records regression tests and 25 same-author synthetic development cases. These do not estimate real-world accuracy. The private evaluation structure exists; an independently authored evaluation dataset is still needed. Engine timings and scripted audio timestamps do not establish live speech-to-alert latency.

Next: connect the microphone stream to the scoped confirmation workflow, introduce real reviewer enrollment, and measure live alert latency and actual service cost for that path.

## Reference material

- [Run and API details](docs/V2_PHASE1.md)
- [Local results](scambench/LOCAL_RESULTS.md)
- [Build history and disclosure](BUILD_LOG.md)

The remaining documents in `docs/`, including architecture, threat model, product strategy and pitch plans, are design/reference material. Their future capabilities are not implementation claims. Original research is preserved at commit `16c469ae78f22f06df757595b8b36edd9359086e`.

## License

[MIT](LICENSE). Reused libraries and models retain their respective licenses and attribution.
