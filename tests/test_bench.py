from callgate.bench import evaluate


def test_reports_failures_without_hiding_them():
    report = evaluate("scambench/scenarios.jsonl")
    assert report["cases"] == 12
    rows = {r["id"]: r for r in report["rows"]}
    assert rows["paraphrase-miss"]["state_pass"]
    assert not rows["quoted-warning"]["false_intervention"]
    assert rows["family-secrecy"]["first_alert_audio_ms"] == 1000
    assert report["engine_p95_ms"] >= 0
