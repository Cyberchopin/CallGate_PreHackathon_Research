"""Bounded in-memory demo measurements; no audio, transcript, or identifiers."""
import math
import threading
from collections import deque


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(fraction * len(ordered)) - 1]


class LiveMetrics:
    def __init__(self, capacity=100):
        if type(capacity) is not int or not 1 <= capacity <= 10_000:
            raise ValueError('invalid metrics capacity')
        self._rows = deque(maxlen=capacity)
        self._lock = threading.Lock()

    def record(self, *, completed, audio_ms, first_alert_proxy_ms, risk_engine_ms):
        row = {
            'completed': bool(completed),
            'audio_ms': max(0.0, float(audio_ms)),
            'first_alert_proxy_ms': (None if first_alert_proxy_ms is None else
                                     max(0.0, float(first_alert_proxy_ms))),
            'risk_engine_ms': (None if risk_engine_ms is None else
                               max(0.0, float(risk_engine_ms))),
        }
        with self._lock:
            self._rows.append(row)

    def summary(self):
        with self._lock:
            rows = list(self._rows)
        completed = sum(row['completed'] for row in rows)
        alerts = [row['first_alert_proxy_ms'] for row in rows
                  if row['first_alert_proxy_ms'] is not None]
        engines = [row['risk_engine_ms'] for row in rows
                   if row['risk_engine_ms'] is not None]
        return {
            'sessions': len(rows),
            'completed': completed,
            'failed': len(rows) - completed,
            'failure_rate': None if not rows else (len(rows)-completed)/len(rows),
            'alert_samples': len(alerts),
            'alert_proxy_p50_ms': percentile(alerts, .50),
            'alert_proxy_p95_ms': percentile(alerts, .95),
            'risk_engine_p50_ms': percentile(engines, .50),
            'risk_engine_p95_ms': percentile(engines, .95),
            'scope': 'current_process_bounded_no_content',
        }
