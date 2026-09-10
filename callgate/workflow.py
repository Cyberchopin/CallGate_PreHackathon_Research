"""Trusted local orchestration for a demo action, not real identity enrollment."""
import hashlib
import json
import secrets
import threading

from .engine import Conversation


class DemoWorkflow:
    def __init__(self, coordinator, gate, reviewer):
        self._coordinator = coordinator
        self._gate = gate
        self._reviewer = reviewer
        self._conversation = Conversation()
        self._session = secrets.token_hex(16)
        self._pending = None
        self._lock = threading.Lock()

    def ingest(self, transcript):
        with self._lock:
            result = self._conversation.ingest(transcript)
            if result['status'] == 'accepted':
                self._pending = None
            return result

    def request_confirmation(self, *, destination, amount_cents):
        # Operation comes from the trusted application, never extracted speech.
        if not isinstance(destination, str) or not destination.strip() or len(destination) > 80:
            raise ValueError('invalid destination')
        if type(amount_cents) is not int or not 0 < amount_cents <= 100_000_000:
            raise ValueError('invalid amount')
        with self._lock:
            if self._conversation.state != 'CHALLENGED':
                raise ValueError('policy requires a challenged conversation')
            operation = dict(destination=destination, amount_cents=amount_cents, currency='USD')
            resource = hashlib.sha256(json.dumps(operation, sort_keys=True).encode()).hexdigest()
            request = self._coordinator.create(session_id=self._session, resource=resource,
                                               reviewer=self._reviewer)
            self._pending = (request, operation)
            return {'request': request, 'operation': dict(operation)}

    def complete(self, decision):
        with self._lock:
            if self._pending is None or decision.request != self._pending[0]:
                raise ValueError('no matching current confirmation')
            if self._conversation.state != 'CHALLENGED':
                raise ValueError('policy denies action')
            request, operation = self._pending
            credential = self._coordinator.decide(decision)
            self._pending = None
            if credential is None:
                return {'status': 'reviewer_denied', 'real_action_executed': False}
            result = self._gate.execute(credential, session_id=self._session,
                resource=request.resource, human_confirmed=True, policy_allows=True)
            return {**result, 'operation': dict(operation)}
