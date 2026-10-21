"""Text-to-speech with Piper (free, runs locally on the CPU).

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


def synthesize(sentences: list[str], voice_path: Path, out_wav: Path, gap: float) -> list[Segment]:
    from piper import PiperVoice  # imported here so tests of other modules don't need Piper

    if not voice_path.exists():
        raise FileNotFoundError(
            f"Piper voice not found: {voice_path}. Download it with "
            "`python -m piper.download_voices en_US-lessac-medium --data-dir voices`."
        )
    voice = PiperVoice.load(voice_path)

    pieces: list[np.ndarray] = []
    segments: list[Segment] = []
    sample_rate = None
    t = 0.0
    for sentence in sentences:
        chunks = list(voice.synthesize(sentence))
        if not chunks:
            continue
        sample_rate = chunks[0].sample_rate
        audio = np.concatenate([c.audio_int16_array for c in chunks])
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
