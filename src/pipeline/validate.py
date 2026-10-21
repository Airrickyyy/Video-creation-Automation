"""Check a rendered video before it goes into the review queue."""

import json
import re
import subprocess
from pathlib import Path

from ..config import Settings

SILENCE_DB = -45.0  # mean volume below this means the narration is effectively missing


def probe(path: Path, settings: Settings) -> dict:
    out = subprocess.run(
        [settings.ffprobe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def analyze(path: Path, settings: Settings) -> tuple[float | None, list[float]]:
    """Return (mean audio volume in dB, start times of black stretches >= 1s)."""
    out = subprocess.run(
        [settings.ffmpeg, "-hide_banner", "-i", str(path),
         "-vf", "blackdetect=d=1:pix_th=0.10", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    vol = re.search(r"mean_volume:\s*(-?[\d.]+) dB", out.stderr)
    blacks = [float(x) for x in re.findall(r"black_start:([\d.]+)", out.stderr)]
    return (float(vol.group(1)) if vol else None), blacks


def validate(path: Path, expected_duration: float, settings: Settings) -> dict:
    checks: dict[str, dict] = {}

    def check(name: str, ok: bool, detail) -> None:
        checks[name] = {"ok": bool(ok), "detail": detail}

    if not path.exists() or path.stat().st_size == 0:
        check("file_exists", False, str(path))
        return {"passed": False, "checks": checks}
    check("file_exists", True, f"{path.stat().st_size} bytes")

    info = probe(path, settings)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    duration = float(info["format"].get("duration", 0))

    check("video_stream", video is not None, video and video["codec_name"])
    check("dimensions", video is not None and (video["width"], video["height"]) == (settings.width, settings.height),
          video and f"{video['width']}x{video['height']}")
    check("audio_stream", audio is not None, audio and audio["codec_name"])
    check("duration_matches_narration", abs(duration - expected_duration) < 0.5,
          f"{duration:.2f}s (narration {expected_duration:.2f}s)")
    check("duration_limit", 0 < duration <= settings.max_duration, f"{duration:.2f}s / max {settings.max_duration}s")

    mean_db, blacks = analyze(path, settings)
    check("audio_not_silent", mean_db is not None and mean_db > SILENCE_DB, f"mean volume {mean_db} dB")
    check("no_black_frames", not blacks, f"black stretches at {blacks}" if blacks else "none")

    return {"passed": all(c["ok"] for c in checks.values()), "checks": checks}
