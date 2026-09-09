"""Stream a consented/synthetic WAV to AssemblyAI and record risk events, not keys."""
import argparse
import asyncio
import json
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from callgate.assemblyai import stream_pcm
from callgate.engine import Conversation


async def run(audio_path, output_path):
    env_path = Path(__file__).resolve().parents[1] / ".env"
    key = next(line.split("=", 1)[1].strip() for line in env_path.read_text(encoding="utf-8-sig").splitlines()
               if line.startswith("ASSEMBLYAI_API_KEY="))
    engine = Conversation()
    updates = []
    started = time.perf_counter()

    async def chunks():
        with wave.open(str(audio_path), "rb") as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
                raise ValueError("Expected mono PCM16 16kHz WAV")
            while data := audio.readframes(1600):
                yield data.ljust(3200, b"\0")
                await asyncio.sleep(.1)
        # Let the provider finalize the last spoken turn before termination.
        for _ in range(25):
            yield b"\0" * 3200
            await asyncio.sleep(.1)

    async def capture(segment):
        result = engine.ingest(segment)
        updates.append({"received_ms": round((time.perf_counter()-started)*1000),
                        "transcript": segment.model_dump(), "risk": result})
        if segment.final:
            print(json.dumps({"transcript": segment.text, "state": result["state"],
                              "score": result["score"], "guardian": result["guardian"]["action"]}), flush=True)

    await asyncio.wait_for(stream_pcm(chunks(), capture, api_key=key), timeout=90)
    if not any(item["transcript"]["final"] for item in updates):
        raise RuntimeError("No finalized transcript received")
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "audio": str(audio_path.name),
              "test_type": "live_provider_synthetic_audio", "updates": updates,
              "final": engine.snapshot(), "wall_seconds": round(time.perf_counter()-started, 2),
              "limitations": "Synthetic clean speech smoke test; not held-out accuracy or microphone/telephony verification."}
    output_path.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("REPORT_SAVED", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        asyncio.run(run(args.audio, args.output))
    except Exception as exc:
        # No provider exception strings: they can include connection metadata.
        print("SMOKE_FAILED: " + type(exc).__name__)
        raise SystemExit(1)
