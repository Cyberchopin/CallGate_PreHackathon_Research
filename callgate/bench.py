"""Synthetic development smoke benchmark, not a generalization claim."""
import argparse
import hashlib
import json
import math
import platform
import time
from pathlib import Path
from .models import Transcript
from .engine import Conversation, EXTRACTOR_VERSION


def evaluate(path):
    raw = Path(path).read_bytes()
    cases = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("benchmark must contain unique cases")
    rows, latencies = [], []
    tp = fp = fn = tn = 0
    for case in cases:
        engine = Conversation()
        first_alert = None
        actual = set()
        for data in case["segments"]:
            start = time.perf_counter()
            result = engine.ingest(Transcript.model_validate(data))
            latencies.append((time.perf_counter()-start)*1000)
            actual = {e["kind"] for e in result["events"]}
            if first_alert is None and result["state"] != "UNVERIFIED":
                first_alert = data["end_ms"]
        expected = set(case["expected_events"])
        tp += len(actual & expected); fp += len(actual-expected); fn += len(expected-actual)
        predicted_alert = result["state"] != "UNVERIFIED"
        rows.append(dict(id=case["id"], slice=case["slice"], state=result["state"],
            expected_state=case["expected_state"], state_pass=result["state"] == case["expected_state"],
            missing_events=sorted(expected-actual), extra_events=sorted(actual-expected),
            benign=case["benign"], false_intervention=case["benign"] and predicted_alert,
            first_alert_audio_ms=first_alert,
            detection_delay_ms=None if first_alert is None or case.get("risk_onset_ms") is None else first_alert-case["risk_onset_ms"]))
    benign = [r for r in rows if r["benign"]]
    return dict(dataset_sha256=hashlib.sha256(raw).hexdigest(), cases=len(rows),
        corpus="synthetic-dev-smoke-v1", limitations="Same-author development cases; no held-out accuracy or audio latency claim.",
        extractor=EXTRACTOR_VERSION, policy="v2-phase1", python=platform.python_version(), platform=platform.platform(),
        event_precision=tp/(tp+fp) if tp+fp else None,
        event_recall=tp/(tp+fn) if tp+fn else None,
        false_intervention_rate=sum(r["false_intervention"] for r in benign)/len(benign) if benign else None,
        state_passes=sum(r["state_pass"] for r in rows),
        engine_p95_ms=sorted(latencies)[math.ceil(.95*len(latencies))-1], rows=rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="scambench/scenarios.jsonl")
    parser.add_argument("--output", default="scambench/results.json")
    args = parser.parse_args()
    result = evaluate(args.dataset)
    Path(args.output).write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, indent=2))
