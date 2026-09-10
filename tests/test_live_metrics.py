import pytest

from callgate.live_metrics import LiveMetrics


def test_empty_and_percentile_summary_without_content_fields():
    metrics = LiveMetrics(capacity=3)
    assert metrics.summary()['failure_rate'] is None
    metrics.record(completed=True, audio_ms=1000, first_alert_proxy_ms=100,
                   risk_engine_ms=.2)
    metrics.record(completed=False, audio_ms=2000, first_alert_proxy_ms=None,
                   risk_engine_ms=None)
    metrics.record(completed=True, audio_ms=3000, first_alert_proxy_ms=300,
                   risk_engine_ms=.4)
    metrics.record(completed=True, audio_ms=4000, first_alert_proxy_ms=200,
                   risk_engine_ms=.3)
    result = metrics.summary()
    assert result['sessions'] == 3
    assert result['completed'] == 2 and result['failed'] == 1
    assert result['failure_rate'] == pytest.approx(1/3)
    assert result['alert_proxy_p50_ms'] == 200
    assert result['alert_proxy_p95_ms'] == 300
    assert set(result).isdisjoint({'transcript', 'audio', 'challenge', 'session_id'})


@pytest.mark.parametrize('capacity', [0, -1, 1.5, 10001])
def test_capacity_is_bounded(capacity):
    with pytest.raises(ValueError):
        LiveMetrics(capacity)
