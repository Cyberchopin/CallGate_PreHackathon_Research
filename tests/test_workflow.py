import pytest
pytest.importorskip('cryptography')
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from callgate.confirmation import ConfirmationCoordinator, ReviewerDecision, decision_bytes
from callgate.verification import DemoVerificationGate
from callgate.workflow import DemoWorkflow
from callgate.models import Transcript


def setup():
    issuer, reviewer = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    clock = [1000]
    coordinator = ConfirmationCoordinator('issuer', issuer, {'reviewer': reviewer.public_key()},
                                           clock=lambda: clock[0])
    gate = DemoVerificationGate({'issuer': issuer.public_key()}, clock=lambda: clock[0])
    workflow = DemoWorkflow(coordinator, gate, 'reviewer')
    workflow.ingest(Transcript(segment_id='s', text='Move your savings into the secure holding wallet.',
                               final=True, start_ms=0, end_ms=1000))
    bundle = workflow.request_confirmation(destination='demo-wallet', amount_cents=280000)
    return workflow, reviewer, bundle, clock


def sign(key, bundle, approved=True):
    request = bundle['request']
    return ReviewerDecision(request=request, approved=approved,
        signature=key.sign(decision_bytes(request, approved)).hex())


def test_complete_once():
    workflow, reviewer, bundle, _ = setup()
    decision = sign(reviewer, bundle)
    result = workflow.complete(decision)
    assert result['status'] == 'simulated_action_completed'
    assert result['operation']['amount_cents'] == 280000
    assert result['real_action_executed'] is False
    with pytest.raises(ValueError):
        workflow.complete(decision)


def test_forged_and_expired_confirmation():
    workflow, reviewer, bundle, clock = setup()
    with pytest.raises(ValueError, match='signature'):
        workflow.complete(sign(Ed25519PrivateKey.generate(), bundle))
    clock[0] += 121
    with pytest.raises(ValueError, match='expired'):
        workflow.complete(sign(reviewer, bundle))


def test_new_evidence_invalidates_and_secrecy_blocks():
    workflow, reviewer, bundle, _ = setup()
    workflow.ingest(Transcript(segment_id='s2', text='Do not tell anyone.', final=True,
                               start_ms=1000, end_ms=2000))
    with pytest.raises(ValueError):
        workflow.complete(sign(reviewer, bundle))
    with pytest.raises(ValueError, match='policy'):
        workflow.request_confirmation(destination='demo-wallet', amount_cents=280000)


def test_denial_and_cross_session():
    workflow, reviewer, bundle, _ = setup()
    other, _, _, _ = setup()
    with pytest.raises(ValueError):
        other.complete(sign(reviewer, bundle))
    assert workflow.complete(sign(reviewer, bundle, False))['status'] == 'reviewer_denied'
