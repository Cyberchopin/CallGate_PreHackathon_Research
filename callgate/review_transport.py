"""Two loopback applications with separate capabilities; no human identity proof.

The broker owns the issuer and policy. Only the reviewer process holds the
reviewer signing key. Both processes and their host remain trusted.
"""
import hashlib
import hmac
import json
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import Field

from .confirmation import ConfirmationRequest, ReviewerDecision, decision_bytes
from .models import StrictModel, Transcript

ASSETS = Path(__file__).parent / 'demo'


class Operation(StrictModel):
    destination: str = Field(min_length=1, max_length=80)
    amount_cents: int = Field(gt=0, le=100_000_000)


class Approval(StrictModel):
    request_id: str = Field(pattern=r'^[a-f0-9]{64}$')
    approved: bool
    challenge_response: str | None = Field(default=None, pattern=r'^\d{6}$')


class SubmittedDecision(StrictModel):
    decision: ReviewerDecision
    challenge_response: str | None = Field(default=None, pattern=r'^\d{6}$')


class ProcessingConsent(StrictModel):
    granted: bool


def guarded_app(origin, page):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    host = urlsplit(origin).netloc

    @app.middleware('http')
    async def boundary(request: Request, call_next):
        if request.headers.get('host') != host:
            return JSONResponse({'detail': 'invalid host'}, status_code=400)
        supplied = request.headers.get('origin')
        if supplied is not None and supplied != origin:
            return JSONResponse({'detail': 'invalid origin'}, status_code=403)
        # Authenticated Python-to-Python calls omit Origin; browsers cannot set
        # Authorization cross-origin without a preflight, which we do not allow.
        response = await call_next(request)
        response.headers.update({
            'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        })
        return response

    @app.get('/')
    def index():
        return FileResponse(ASSETS / page)

    @app.get('/review-ui.js')
    def javascript():
        return FileResponse(ASSETS / 'review-ui.js', media_type='text/javascript')

    @app.get('/review-ui.css')
    def css():
        return FileResponse(ASSETS / 'review-ui.css', media_type='text/css')

    return app


def bearer(token):
    def require(request: Request):
        header = request.headers.get('authorization', '')
        if not hmac.compare_digest(header.encode(), ('Bearer ' + token).encode()):
            raise HTTPException(401, 'role credential required')
    return require


def create_broker_app(workflow, participant_token, reviewer_token, *, origin='http://127.0.0.1:8766'):
    if not participant_token or not reviewer_token or participant_token == reviewer_token:
        raise ValueError('distinct role credentials required')
    app = guarded_app(origin, 'participant.html')
    participant, reviewer = bearer(participant_token), bearer(reviewer_token)

    @app.get('/api/status', dependencies=[Depends(participant)])
    def status():
        return workflow.status()

    @app.post('/api/processing-consent', dependencies=[Depends(participant)])
    def processing_consent(body: ProcessingConsent):
        return workflow.set_processing_consent(body.granted)

    @app.post('/api/transcript', dependencies=[Depends(participant)])
    def ingest(body: Transcript):
        try:
            return workflow.ingest(body)
        except ValueError:
            raise HTTPException(409, 'transcript rejected') from None

    @app.post('/api/request', dependencies=[Depends(participant)])
    def request_confirmation(body: Operation):
        try:
            return workflow.request_confirmation(**body.model_dump())
        except ValueError:
            raise HTTPException(409, 'policy prevents confirmation') from None

    @app.get('/api/review/pending', dependencies=[Depends(reviewer)])
    def pending():
        return workflow.pending_confirmation()

    @app.post('/api/review/decision', dependencies=[Depends(reviewer)])
    def decision(body: SubmittedDecision):
        try:
            return workflow.complete(body.decision, challenge_response=body.challenge_response)
        except ValueError:
            raise HTTPException(409, 'confirmation invalid, stale, expired or already used') from None

    return app


def create_reviewer_app(signing_key, reviewer_token, fetch_pending, submit_decision, *,
                        origin='http://127.0.0.1:8767'):
    if not reviewer_token:
        raise ValueError('reviewer credential required')
    app = guarded_app(origin, 'reviewer.html')
    reviewer = bearer(reviewer_token)

    def fetch_verified():
        try:
            bundle = fetch_pending()
        except Exception:
            raise HTTPException(503, 'confirmation channel unavailable') from None
        try:
            if bundle is None:
                return None
            request = ConfirmationRequest.model_validate(bundle['request'])
            operation = dict(bundle['operation'])
            if operation.pop('currency') != 'USD':
                raise ValueError('unsupported currency')
            operation = {**Operation.model_validate(operation).model_dump(), 'currency': 'USD'}
            digest = hashlib.sha256(json.dumps(operation, sort_keys=True).encode()).hexdigest()
            if not hmac.compare_digest(digest, request.resource):
                raise ValueError('operation commitment mismatch')
            return {'request': request, 'operation': operation}
        except (ValueError, KeyError, TypeError):
            # No upstream exception, transcript or credential in a client error.
            raise HTTPException(409, 'confirmation content invalid') from None

    @app.get('/api/pending', dependencies=[Depends(reviewer)])
    def pending():
        return fetch_verified()

    @app.post('/api/decide', dependencies=[Depends(reviewer)])
    def decide(body: Approval):
        bundle = fetch_verified()
        if bundle is None or bundle['request'].request_id != body.request_id:
            raise HTTPException(409, 'reviewed request is no longer current')
        request = bundle['request']
        signed = ReviewerDecision(request=request, approved=body.approved,
            signature=signing_key.sign(decision_bytes(request, body.approved)).hex())
        try:
            return submit_decision(SubmittedDecision(
                decision=signed, challenge_response=body.challenge_response))
        except ValueError:
            raise HTTPException(409, 'confirmation invalid, stale, expired or already used') from None
        except Exception:
            # A lost response may follow a completed simulated action. Never
            # retry or claim success; the broker consumes confirmation once.
            raise HTTPException(503, 'decision not confirmed; do not retry automatically') from None

    return app
