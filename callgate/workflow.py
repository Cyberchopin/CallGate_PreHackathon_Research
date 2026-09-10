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
        self._generation = 0
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
                self._generation += 1
                self._processing_consent = ('REVOKED' if self._processing_consent == 'GRANTED'
                                            else 'DECLINED')
                self._invalidate()
                self._conversation = Conversation()
                self._outcome = None
            return {'processing_consent': self._processing_consent,
                    'processing_allowed': self._processing_consent == 'GRANTED'}

    def reset_session(self):
        """End the current scenario and require fresh consent for a new one."""
        with self._lock:
            self._generation += 1
            self._invalidate()
            self._conversation = Conversation()
            self._session = secrets.token_hex(16)
            self._outcome = None
            self._processing_consent = 'NOT_REQUESTED'
            return {'risk_state': self._conversation.state,
                    'processing_consent': self._processing_consent,
                    'processing_allowed': False, 'pending': False, 'outcome': None}

    def processing_generation(self):
        with self._lock:
            if self._processing_consent != 'GRANTED':
                raise ValueError('processing consent required')
            return self._generation

    def ingest(self, transcript, *, generation=None):
        with self._lock:
            if generation is not None and generation != self._generation:
                raise ValueError('stale audio session')
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
            request, operation, _, _ = self._pending
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
            challenge = f'{secrets.randbelow(1_000_000):06d}'
            challenge_digest = hashlib.sha256(
                (self._session + request.request_id + challenge).encode()).digest()
            self._pending = (request, operation, challenge_digest, 0)
            self._outcome = None
            return {'request': request, 'operation': dict(operation),
                    'out_of_band_challenge': challenge}

    def complete(self, decision, *, challenge_response=None):
        with self._lock:
            if self._pending is None or decision.request != self._pending[0]:
                raise ValueError('no matching current confirmation')
            if self._conversation.state != 'CHALLENGED':
                raise ValueError('policy denies action')
            request, operation, expected_challenge, attempts = self._pending
            if decision.approved:
                supplied = '' if challenge_response is None else str(challenge_response)
                actual = hashlib.sha256(
                    (self._session + request.request_id + supplied).encode()).digest()
                if not secrets.compare_digest(actual, expected_challenge):
                    attempts += 1
                    if attempts >= 3:
                        self._invalidate()
                    else:
                        self._pending = (request, operation, expected_challenge, attempts)
                    raise ValueError('invalid out-of-band challenge')
            credential = self._coordinator.decide(decision)
            self._pending = None
            if credential is None:
                self._outcome = {'status': 'reviewer_denied', 'real_action_executed': False}
                return dict(self._outcome)
            result = self._gate.execute(credential, session_id=self._session,
                resource=request.resource, human_confirmed=True, policy_allows=True)
            self._outcome = {**result, 'operation': dict(operation)}
            return dict(self._outcome)
