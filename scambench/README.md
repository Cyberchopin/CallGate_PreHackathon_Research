# ScamBench development skeleton

Run `python -m callgate.bench`. Cases are original synthetic examples under this repository's MIT license, not real victim calls. This is a development smoke corpus, not a held-out research benchmark.

Each JSONL case includes `id`, `slice`, `benign`, ordered transcript `segments`, `expected_events`, `expected_state`, and optional `risk_onset_ms`. The evaluator reports event precision/recall, benign false interventions, state matches, first alert on the audio clock, and engine-only p95 compute time with dataset hash and environment. No network/STT latency is included.

Next: independently authored held-out dialogues, paraphrases, multi-speaker attribution, code-switching, quoted warnings, codec/noise slices, partial revisions, delayed provider events and attack onset annotations. Split by scenario family and speaker, not randomly by turn. Keep train/dev/test separated and version annotations. Measure missed high-impact actions and interventions before requested action completion, not just final binary accuracy.

Known failure probes remain in the corpus deliberately. A good score on these examples does not establish deployment safety. ASVspoof audio is a separate acoustic evaluation track; do not merge its EER with conversational scam precision.
