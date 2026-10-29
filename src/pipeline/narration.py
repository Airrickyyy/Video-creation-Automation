"""Text-to-speech with Piper or Kokoro (both free, run locally on the CPU; Kokoro sounds more natural).

Each sentence is synthesized separately so we know exactly when it starts and
ends in the final audio; captions are timed from that, no speech recognition needed.
"""

import re
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Segment:
    text: str
    start: float
    end: float


def split_sentences(script: str) -> list[str]:
    text = re.sub(r"\s+", " ", script).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def split_shots(script: str) -> list[list[str]]:
    """Blank-line-separated paragraphs, each a list of sentences (one visual per paragraph)."""
    paragraphs = re.split(r"\n\s*\n", script.strip())
    return [s for s in (split_sentences(p) for p in paragraphs) if s]


def _piper(voice_path: Path, speed: float):
    from piper import PiperVoice, SynthesisConfig  # imported here so other modules' tests don't need Piper

    if not voice_path.exists():
        raise FileNotFoundError(
            f"Piper voice not found: {voice_path}. Download it with "
            "`python -m piper.download_voices en_US-lessac-medium --data-dir voices`."
        )
    voice = PiperVoice.load(voice_path)
    config = SynthesisConfig(length_scale=1 / speed)

    def speak(text: str) -> tuple[np.ndarray, int] | None:
        chunks = list(voice.synthesize(text, config))
        if not chunks:
            return None
        return np.concatenate([c.audio_int16_array for c in chunks]), chunks[0].sample_rate
    return speak


def _kokoro(model_path: Path, voice_name: str, speed: float):
    from kokoro_onnx import Kokoro

    voices_path = model_path.parent / "voices-v1.0.bin"
    for f in (model_path, voices_path):
        if not f.exists():
            raise FileNotFoundError(
                f"Kokoro file not found: {f}. Download it from "
                "https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 into voices/."
            )
    kokoro = Kokoro(str(model_path), str(voices_path))

    def speak(text: str) -> tuple[np.ndarray, int] | None:
        samples, sample_rate = kokoro.create(text, voice=voice_name, speed=speed, lang="en-us")
        if len(samples) == 0:
            return None
        return (np.clip(samples, -1, 1) * 32767).astype(np.int16), sample_rate
    return speak


def synthesize(sentences: list[str], out_wav: Path, gap: float, speed: float = 1.0, engine: str = "piper",
               piper_voice: Path | None = None, kokoro_model: Path | None = None,
               kokoro_voice: str = "af_heart") -> list[Segment]:
    """engine is "piper" or "kokoro". speed > 1 talks faster (1.4 is roughly the ~280 words/minute
    of popular story channels)."""
    if engine == "kokoro":
        speak = _kokoro(kokoro_model, kokoro_voice, speed)
    elif engine == "piper":
        speak = _piper(piper_voice, speed)
    else:
        raise ValueError(f"Unknown voice_engine {engine!r} (use \"piper\" or \"kokoro\")")

    pieces: list[np.ndarray] = []
    segments: list[Segment] = []
    sample_rate = None
    t = 0.0
    for sentence in sentences:
        spoken = speak(sentence.replace("*", ""))  # *highlight* marks are captions-only
        if spoken is None:
            continue
        audio, sample_rate = spoken
        duration = len(audio) / sample_rate
        segments.append(Segment(sentence, t, t + duration))
        silence = np.zeros(int(gap * sample_rate), dtype=np.int16)
        pieces.extend([audio, silence])
        t += duration + gap

    if not segments:
        raise ValueError("Script produced no audio (is it empty?)")

    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(np.concatenate(pieces).tobytes())
    return segments
