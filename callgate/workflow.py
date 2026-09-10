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
        self._outcome = None
        self._processing_consent = 'NOT_REQUESTED'
        self._lock = threading.Lock()

    def _invalidate(self):
        if self._pending is not None:
            self._coordinator.cancel(self._pending[0].request_id)
        self._pending = None

    def status(self):
        with self._lock:
            return {'risk_state': self._conversation.state,
                    'processing_consent': self._processing_consent,
                    'processing_allowed': self._processing_consent == 'GRANTED',
                    'pending': self._pending is not None,
                    'outcome': None if self._outcome is None else dict(self._outcome)}

    def set_processing_consent(self, granted):
        """Apply an explicit per-session processing choice.

        Declining or withdrawing is fail-closed: current evidence and any pending
        action are discarded. This is a product control, not a legal conclusion.
        """
        if type(granted) is not bool:
            raise ValueError('invalid consent choice')
        with self._lock:
            if granted:
                self._processing_consent = 'GRANTED'
            else:
                self._processing_consent = ('REVOKED' if self._processing_consent == 'GRANTED'
                                            else 'DECLINED')
                self._invalidate()
                self._conversation = Conversation()
                self._outcome = None
            return {'processing_consent': self._processing_consent,
                    'processing_allowed': self._processing_consent == 'GRANTED'}

    def ingest(self, transcript):
        with self._lock:
            if self._processing_consent != 'GRANTED':
                raise ValueError('processing consent required')
            result = self._conversation.ingest(transcript)
            if result['status'] == 'accepted':
                self._invalidate()
            return result

    def pending_confirmation(self):
        """Read-only view for the authenticated reviewer transport."""
        with self._lock:
            if self._pending is None:
                return None
            request, operation = self._pending
            return {'request': request.model_dump(), 'operation': dict(operation)}

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
            self._invalidate()
            request = self._coordinator.create(session_id=self._session, resource=resource,
                                               reviewer=self._reviewer)
            self._pending = (request, operation)
            self._outcome = None
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
                self._outcome = {'status': 'reviewer_denied', 'real_action_executed': False}
                return dict(self._outcome)
            result = self._gate.execute(credential, session_id=self._session,
                resource=request.resource, human_confirmed=True, policy_allows=True)
            self._outcome = {**result, 'operation': dict(operation)}
            return dict(self._outcome)
