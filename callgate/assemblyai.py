"""AssemblyAI v3 adapter. Turn IDs/revisions belong to the ingress adapter."""
import asyncio
import json
import os
from websockets.asyncio.client import connect
from .models import Transcript


class AssemblyTurns:
    def __init__(self, speaker_roles=None):
        self.previous = {}
        self.speaker_roles = dict(speaker_roles or {})
        if any(role not in {"caller", "recipient"} for role in self.speaker_roles.values()):
            raise ValueError("invalid trusted speaker role mapping")

    def normalize(self, message):
        if message.get("type") != "Turn":
            return None
        order = message["turn_order"]
        if type(order) is not int or order < 0:
            raise ValueError("invalid turn order")
        words = message.get("words") or []
        text = message["transcript"]
        final = message.get("end_of_turn", False)
        label = message.get("speaker_label")
        if label == "UNKNOWN":
            label = None
        if label is not None and (not isinstance(label, str) or not label or len(label) > 16 or not label.replace("_","").replace("-","").isalnum()):
            raise ValueError("invalid speaker label")
        word_labels = {w.get("speaker") for w in words if w.get("word_is_final") and w.get("speaker") not in {None,"UNKNOWN"}}
        # A dominant turn label cannot safely represent two speakers in one turn.
        mixed = len(word_labels) > 1
        role = "unknown" if mixed or label is None else self.speaker_roles.get(label, "unknown")
        old = self.previous.get(order)
        signature = (text, final, label, tuple(sorted(word_labels)))
        if old and old[0] == signature:
            return None
        revision = old[1] + 1 if old else 0
        segment = Transcript(segment_id=f"aai-{order}", revision=revision, text=text,
            start_ms=words[0]["start"] if words else 0,
            end_ms=words[-1]["end"] if words else 0, final=final,
            language=message.get("language_code") or "en", role=role,
            provider_speaker=None if mixed else label)
        self.previous[order] = (signature, revision)
        return segment


async def stream_pcm(chunks, on_segment, connector=connect, api_key=None, speaker_roles=None):
    """Stream 16kHz mono PCM16 chunks; bounded provider queues and 10s final drain."""
    key = api_key or os.environ.get("ASSEMBLYAI_API_KEY")
    if not key:
        raise ValueError("ASSEMBLYAI_API_KEY is required")
    url = "wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&speech_model=universal-streaming-english&format_turns=true&speaker_labels=true&max_speakers=2"
    normalizer = AssemblyTurns(speaker_roles=speaker_roles)
    async with connector(url, additional_headers={"Authorization": key}, max_queue=16,
                         open_timeout=10, close_timeout=3) as ws:
        async def send():
            async for chunk in chunks:
                if not isinstance(chunk, bytes) or not 1600 <= len(chunk) <= 32000 or len(chunk) % 2:
                    raise ValueError("PCM chunks must contain 50-1000ms of mono 16kHz PCM16")
                await ws.send(chunk)
            await ws.send(json.dumps({"type": "Terminate"}))

        async def receive():
            async for raw in ws:
                message = json.loads(raw)
                if message.get("type") == "Termination":
                    return
                if message.get("type") == "Error" or message.get("error"):
                    raise RuntimeError("speech provider error")
                segment = normalizer.normalize(message)
                if segment:
                    await on_segment(segment)

        sender = asyncio.create_task(send())
        receiver = asyncio.create_task(receive())
        try:
            done, _ = await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
            if sender in done:
                await asyncio.wait_for(receiver, timeout=10)
            else:
                raise RuntimeError("speech stream ended before audio input")
        finally:
            for task in (sender, receiver):
                if not task.done():
                    task.cancel()
            await asyncio.gather(sender, receiver, return_exceptions=True)
