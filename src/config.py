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
    width: int = 1080
    height: int = 1920
    fps: int = 30
    max_duration: float = 60.0
    sentence_gap: float = 0.25
    font: str = "Arial"
    font_size: int = 84
    words_per_caption: int = 4
    zoom: float = 0.12  # how far still images zoom over their slice (0 = static)

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        voice = Path(os.environ.get("PIPER_VOICE", ROOT / "voices" / "en_US-lessac-medium.onnx"))
        if not voice.is_absolute():
            voice = ROOT / voice
        return cls(
            ffmpeg=find_tool("ffmpeg"),
            ffprobe=find_tool("ffprobe"),
            piper_voice=voice,
            max_duration=float(os.environ.get("MAX_DURATION", 60)),
            font=os.environ.get("CAPTION_FONT", "Arial"),
            font_size=int(os.environ.get("CAPTION_FONT_SIZE", 84)),
            words_per_caption=int(os.environ.get("WORDS_PER_CAPTION", 4)),
            zoom=float(os.environ.get("IMAGE_ZOOM", 0.12)),
        )
