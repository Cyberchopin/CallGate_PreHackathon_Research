# CallGate v2 build disclosure

- User request date: 2026-09-08, America/Los_Angeles.
- Research baseline: `16c469ae78f22f06df757595b8b36edd9359086e` (original remote main).
- Working branch: `callgate-v2/phase-1`.
- Scope change: user explicitly requested implementation now for AssemblyAI and AI Infra, with later reuse. Earlier LA Hacks research-only timing is historical, not an instruction to delay this work.
- AI-assisted implementation: Codex implemented the files in `callgate/`, `tests/`, `scripts/`, `scambench/` and v2 documentation in this working session. No third-party implementation source was copied.
- Existing work: all original research documents. New work: English rules baseline, strict schemas, revision-aware state and timeline, advisory Guardian, REST/transcript/audio WebSocket adapters, AssemblyAI v3 normalization, WAV streaming client, tests, synthetic development corpus and evaluator.
- Tests: see `scambench/results.json` and `scambench/test-results.xml`; these are local measurements, not competition or production results.
- External service: AssemblyAI adapter written against official streaming documentation; no live credentialed audio call was run.
- Not built: semantic LLM extractor, speaker role mapping, deepfake model, independent verifier, capability tokens, signed receipts, real payment/phone controls, production auth/deployment.
- Later event disclosure: list this entire baseline as pre-existing when applicable. Do not claim it was built during a future event. Keep event-specific deltas in separate branches and verify sponsor/eligibility rules at submission time.

## Subsequent live provider smoke test

After the user configured the local key and requested continuation, two synthetic English WAVs were streamed at realtime pace through the actual AssemblyAI v3 service and existing Conversation engine. See timestamped `scambench/live-scam.json` and `scambench/live-benign.json`.

- Scam sample: bank claim → immediate money request → secrecy; observed UNVERIFIED → CHALLENGED → COOLING_OFF, score 80, Guardian PAUSE.
- Benign sample: lunch appointment; remained UNVERIFIED, score 0, Guardian LISTEN.
- The synthetic audio was generated using gTTS 2.5.4 and converted using miniaudio 1.71 as test preparation, not product dependencies. The application credential was sent only to AssemblyAI in its authorization header. No microphone or real call was captured.
- Added `scripts/live_smoke.py` for explicit WAV-to-provider-to-engine smoke runs. All 18 existing tests still passed afterward. The local click dependency was resolved to 8.1.8 by the audio preparation tooling and is reflected in the lock file.
- This supersedes the earlier 'no live credentialed audio call' status for these two samples only. It does not establish real-call accuracy, device capture, REST/audio WebSocket end-to-end behavior, or production reliability.

## Local microphone test page

Added a minimal local page with explicit Start/Stop, microphone level, revision-aware transcript, Chinese Guardian messages and state transition list. Added a `.env`-aware launcher, same-origin browser WebSocket checks and restricted static assets. The server returned HTTP 200 at `http://127.0.0.1:8765/`; 20 Python tests passed and both browser JavaScript files passed syntax checks. The two additional tests cover the demo route/origin rejection and the local audio WebSocket pipeline with a simulated provider. Browser/device capture is awaiting user testing; no claim is made that a browser tab or permission popup is visible on the user's screen.

## User microphone feedback and bounded rule repair

The user subsequently reported successful microphone transcripts for the money+secrecy sample (70, COOLING_OFF) and benign lunch sample (0, UNVERIFIED). They also reported an exact transcript of "Move your savings into the secure holding wallet." with score 0, confirming the known paraphrase false negative in the live user flow.

`rules-en-v2` adds a bounded asset-relocation request grammar, covering move/shift/relocate/transfer/send/deposit + savings/funds/balance/etc. + wallet/account. Sentence/request-prefix matching avoids several first-person plans, conditional discussions and negated warnings. This is a rule expansion, not a semantic model, and unfamiliar wording/quotations still need further work. Fourteen additional tests cover variations, benign discussion, negation and cross-turn secrecy; all 34 tests passed. The unchanged 12-case development corpus now has 11 state matches; the quoted-warning false positive remains explicitly reported in `scambench/results-rules-en-v2.json`. The original result file is retained for comparison.

## Open-source reuse integration, 2026-09-08

14 upstream checkouts pinned in docs/upstreams.json. Integrated MIT Silero model and Pipecat 1.8.1 processor boundary; see docs/REUSE_PLAN.md and THIRD_PARTY.md. Optional sensor inference failure preserves raw STT input. 39 tests passed. Real provider/local WebSocket smoke completed with 106 sensor observations and COOLING_OFF decision. Demo restarted with CALLGATE_VAD=silero. Hosted forks remain blocked by expired CLI authentication and signed-out browser; no forks claimed created.

## Context regression update

Extractor rules-en-v3 narrowly recognizes explicit hypothetical scammer examples within one sentence. Contrast and sentence boundaries preserve subsequent action requests; quotes alone do not suppress detection. Responses expose educational_context_heuristic uncertainty and never authorize an action. Eight paired boundary tests added; full suite 47 passed. Original unchanged 12-case development corpus now 12/12 (results-v3.json). This is same-author development validation, not held-out accuracy. Broader paraphrases, punctuation-free speech and genuine semantic attribution remain open.
