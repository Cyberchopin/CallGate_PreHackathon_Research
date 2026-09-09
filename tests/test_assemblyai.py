import asyncio
import json
import pytest
from callgate.assemblyai import AssemblyTurns, stream_pcm


def test_normalizer_revisions():
    adapter = AssemblyTurns()
    message = dict(type="Turn", turn_order=0, transcript="Send", end_of_turn=False)
    assert adapter.normalize(message).revision == 0
    assert adapter.normalize(message) is None
    final = adapter.normalize(dict(message, transcript="Send money", end_of_turn=True))
    assert final.revision == 1 and final.final
    assert adapter.normalize({"type": "Begin"}) is None


def test_transport_contract():
    class Fake:
        def __init__(self):
            self.queue = asyncio.Queue()
            self.sent = []
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def send(self, value):
            self.sent.append(value)
            if isinstance(value, bytes):
                await self.queue.put(json.dumps(dict(type="Turn", turn_order=0, transcript="Send money", end_of_turn=True)))
            else:
                await self.queue.put(json.dumps({"type": "Termination"}))
        def __aiter__(self): return self
        async def __anext__(self): return await self.queue.get()
    fake = Fake()
    seen = []
    def connector(url, **kwargs):
        assert url.startswith("wss://streaming.assemblyai.com/v3/ws?")
        assert kwargs["additional_headers"] == {"Authorization": "test-only"}
        return fake
    async def chunks(): yield b"\0" * 3200
    async def capture(s): seen.append(s)
    asyncio.run(stream_pcm(chunks(), capture, connector=connector, api_key="test-only"))
    assert seen[0].text == "Send money"
    assert json.loads(fake.sent[-1]) == {"type": "Terminate"}


def test_missing_key(monkeypatch):
    monkeypatch.delenv("ASSEMBLYAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        asyncio.run(stream_pcm(None, None))
