"""Settings, loaded from environment variables (and an optional .env file)."""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Minimal .env reader: KEY=VALUE lines. Real environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def find_tool(name: str) -> str:
    """Find ffmpeg/ffprobe: FFMPEG_DIR, then PATH, then winget's install folder."""
    custom_dir = os.environ.get("FFMPEG_DIR")
    if custom_dir:
        candidate = Path(custom_dir) / f"{name}.exe"
        if candidate.exists():
            return str(candidate)
        candidate = Path(custom_dir) / name
        if candidate.exists():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    # winget adds FFmpeg to PATH, but terminals opened before the install don't see it yet.
    winget = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    for candidate in winget.glob(f"Gyan.FFmpeg*/*/bin/{name}.exe"):
        return str(candidate)
    raise FileNotFoundError(
        f"{name} not found. Install it with `winget install Gyan.FFmpeg.Essentials` "
        "or set FFMPEG_DIR in .env."
    )


@dataclass
class Settings:
    ffmpeg: str
    ffprobe: str
    piper_voice: Path
    kokoro_model: Path
    width: int = 1080
    height: int = 1920
    fps: int = 30
    max_duration: float = 60.0
    sentence_gap: float = 0.25
    font: str = "Arial"
    font_size: int = 84
    words_per_caption: int = 4
    zoom: float = 0.12  # how far still images zoom over their slice (0 = static)
    voice_engine: str = "piper"  # "piper" or "kokoro" (more natural)
    kokoro_voice: str = "af_heart"  # see https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
    speech_speed: float = 1.0  # >1 talks faster; 1.4 ≈ the pace of popular story channels
    music: str = ""  # background track: a file (relative to the input folder or project), or "random" for one from music/
    music_volume_db: float = -4.0  # music level before ducking; more negative = quieter
    show_captions: bool = True  # off when the card already shows every word (e.g. chat mode)
    caption_colors: bool = False  # rotate each caption through white/yellow/green/pink
    caption_align: int = 2  # numpad layout: 2 = lower third, 5 = screen center
    caption_margin_v: int = 0  # distance of bottom captions from the bottom edge (0 = a third of the height)
    card_top: int = 380  # where the post card starts, from the top
    card_max_height: int = 1100  # the post card grows up to this, then continues on a fresh page

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        voice = Path(os.environ.get("PIPER_VOICE", ROOT / "voices" / "en_US-lessac-medium.onnx"))
        if not voice.is_absolute():
            voice = ROOT / voice
        kokoro = Path(os.environ.get("KOKORO_MODEL", ROOT / "voices" / "kokoro-v1.0.int8.onnx"))
        if not kokoro.is_absolute():
            kokoro = ROOT / kokoro
        return cls(
            ffmpeg=find_tool("ffmpeg"),
            ffprobe=find_tool("ffprobe"),
            piper_voice=voice,
            kokoro_model=kokoro,
            voice_engine=os.environ.get("VOICE_ENGINE", "piper"),
            kokoro_voice=os.environ.get("KOKORO_VOICE", "af_heart"),
            max_duration=float(os.environ.get("MAX_DURATION", 60)),
            font=os.environ.get("CAPTION_FONT", "Arial"),
            font_size=int(os.environ.get("CAPTION_FONT_SIZE", 84)),
            words_per_caption=int(os.environ.get("WORDS_PER_CAPTION", 4)),
            zoom=float(os.environ.get("IMAGE_ZOOM", 0.12)),
            speech_speed=float(os.environ.get("SPEECH_SPEED", 1.0)),
            music=os.environ.get("MUSIC", ""),
            music_volume_db=float(os.environ.get("MUSIC_VOLUME_DB", -4)),
        )
