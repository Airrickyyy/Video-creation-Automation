"""Burned-in captions as an ASS subtitle file (short, bold, centered word groups).

Words wrapped in *asterisks* in the script are shown in the highlight color.
An optional title card can be shown at the top while the hook is spoken.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from .narration import Segment

HIGHLIGHT = "&H0000E5FF&"  # ASS colors are &HBBGGRR&: this is a warm yellow
# With cycle_colors, captions rotate through white, yellow, green and pink.
CYCLE = ["&H00FFFFFF&", "&H0000E5FF&", "&H0050FF7C&", "&H00C850FF&"]


@dataclass
class Caption:
    text: str  # highlighted words are wrapped individually: "*forty* *dollars*"
    start: float
    end: float


def mark_words(text: str) -> list[str]:
    """Split into words, normalizing highlight spans like "*forty dollars*" to "*forty*" "*dollars*"."""
    words, highlighted = [], False
    for w in text.split():
        if w.startswith("*"):
            highlighted = True
        clean = w.replace("*", "")
        if clean:
            words.append(f"*{clean}*" if highlighted else clean)
        if w.rstrip(".,!?;:'\")").endswith("*"):
            highlighted = False
    return words


def chunk_captions(segments: list[Segment], words_per_caption: int) -> list[Caption]:
    """Split each sentence into small word groups, timed by their share of characters."""
    captions = []
    for seg in segments:
        words = mark_words(seg.text)
        groups = [" ".join(words[i:i + words_per_caption]) for i in range(0, len(words), words_per_caption)]
        lengths = [len(g.replace("*", "")) for g in groups]
        t = seg.start
        for g, n in zip(groups, lengths):
            duration = (seg.end - seg.start) * n / sum(lengths)
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


def ass_text(text: str) -> str:
    text = text.replace("{", "(").replace("}", ")").replace("\\", "/")
    return re.sub(r"\*([^*]+)\*", rf"{{\\c{HIGHLIGHT}}}\1{{\\r}}", text)


def write_ass(captions: list[Caption], path: Path, width: int, height: int, font: str, font_size: int,
              align: int = 2, card: str | None = None, card_end: float = 0.0, margin_v: int = 0,
              cycle_colors: bool = False) -> None:
    """align uses numpad layout: 2 = bottom center, 5 = middle.

    margin_v is how far bottom-aligned captions sit above the bottom edge (0 = a third of the height).
    cycle_colors gives each caption the next color in CYCLE (*highlighted* words stay yellow).
    """
    margin_v = margin_v or height // 3
    # Captions: white text, thick black outline. Card: dark text in an opaque white box near the top.
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,{align},90,90,{margin_v},1
Style: Card,{font},56,&H00141414,&H00141414,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,28,0,8,130,130,{height // 6},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    if card:
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(card_end)},Card,,0,0,0,,{ass_text(card)}")
    for i, c in enumerate(captions):
        color = f"{{\\c{CYCLE[i % len(CYCLE)]}}}" if cycle_colors else ""
        lines.append(f"Dialogue: 0,{ass_time(c.start)},{ass_time(c.end)},Default,,0,0,0,,"
                     f"{color}{ass_text(c.text.upper())}")
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
