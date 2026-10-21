"""Burned-in captions as an ASS subtitle file (short, bold, centered word groups)."""

from dataclasses import dataclass
from pathlib import Path

from .narration import Segment


@dataclass
class Caption:
    text: str
    start: float
    end: float


def chunk_captions(segments: list[Segment], words_per_caption: int) -> list[Caption]:
    """Split each sentence into small word groups, timed by their share of characters."""
    captions = []
    for seg in segments:
        words = seg.text.split()
        groups = [" ".join(words[i:i + words_per_caption]) for i in range(0, len(words), words_per_caption)]
        total_chars = sum(len(g) for g in groups)
        t = seg.start
        for g in groups:
            duration = (seg.end - seg.start) * len(g) / total_chars
            captions.append(Caption(g, t, t + duration))
            t += duration
        captions[-1].end = seg.end  # avoid rounding drift at sentence end
    return captions


def ass_time(seconds: float) -> str:
    cs = round(seconds * 100)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass(captions: list[Caption], path: Path, width: int, height: int, font: str, font_size: int) -> None:
    # White text, thick black outline, bottom-center about a third of the way up the frame.
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,90,90,{height // 3},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for c in captions:
        text = c.text.upper().replace("{", "(").replace("}", ")").replace("\\", "/")
        lines.append(f"Dialogue: 0,{ass_time(c.start)},{ass_time(c.end)},Default,,0,0,0,,{text}")
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
