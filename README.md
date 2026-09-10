# CallGate

A local risk-evidence and two-person authorization protocol prototype for voice requests to move money into a "safe account". It is not a production SDK.

**Current boundary:** Two separate prototypes run today. The microphone demo transcribes test speech and displays advisory risk evidence. The text-replay demo exercises explicit processing consent, risk policy, a two-person confirmation step, and one simulated action. They are not connected. Real human identity enrollment, registered out-of-band contacts, multi-tenant isolation, remote trusted transport, key lifecycle/storage, latency SLA, and enforcement over real tools are not implemented. The microphone demo cannot block a bank transfer or control a phone call.

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

1. Participant: explicitly allow processing of fictional test content, analyze the prefilled safe-account sentence, then submit the fictional amount and destination.
2. The participant receives a six-digit one-time challenge and sends it through a separate demo channel.
3. Reviewer: read the request, check the exact amount and destination, enter the challenge, then approve or deny.
4. Participant: refresh the result. Approval permits one simulated action only. New transcript content or consent withdrawal invalidates pending confirmation; secrecy/credential states prevent a new request.

Each role has a different bearer capability. Approval requires both the reviewer capability and the participant's one-time challenge; the reviewer API cannot read that challenge. Three wrong challenge attempts cancel the request. This is a minimal two-person control, not identity verification: no person or outside contact channel is enrolled, and the two users could collude or share both secrets. The reviewer private key is generated only inside the reviewer process; the participant backend receives its public key. Both processes and the host remain trusted.

Keys and pending state are ephemeral; restart invalidates old entries. This launcher uses an in-memory replay gate and one session per startup. It is a text-replay demo, not yet connected to the microphone stream. Tests exercise real loopback HTTP across both processes, including repeat approval rejection and reviewer unavailability.

## Reuse and project contribution

AssemblyAI supplies streaming transcription; Silero and Pipecat integrations provide optional voice processing components; NetworkX, cryptography and SQLite supply graph, signature and persistence primitives. CallGate adds revision-aware evidence handling, cross-turn action/secrecy rules, advisory policy, and tests of scoped credentials and replay rejection.

This is an integration prototype. Comparative superiority over other projects has not been established. See the [source comparison and reuse notes](docs/V2_RESEARCH.md) for research context.

## Evidence and next milestone

The [local report](scambench/LOCAL_RESULTS.md) records regression tests and 25 same-author synthetic development cases. This is an internal synthetic regression suite despite the legacy `scambench/` directory name; it is not an industry benchmark and does not estimate real-world accuracy. An independently authored, frozen evaluation dataset is still needed. Engine timings and scripted audio timestamps do not establish live speech-to-alert latency.

Next: connect the microphone stream to the scoped two-person workflow, then measure live alert latency, false interventions, and actual service cost. Reviewer identity enrollment and production integration remain later milestones.

## Reference material

- [Run and API details](docs/V2_PHASE1.md)
- [Local results](scambench/LOCAL_RESULTS.md)
- [Build history and disclosure](BUILD_LOG.md)

The remaining documents in `docs/`, including architecture, threat model, product strategy and pitch plans, are design/reference material. Their future capabilities are not implementation claims. Original research is preserved at commit `16c469ae78f22f06df757595b8b36edd9359086e`.

## License

[MIT](LICENSE). Reused libraries and models retain their respective licenses and attribution.
