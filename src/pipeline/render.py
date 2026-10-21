"""Render the vertical MP4 with FFmpeg: visuals + narration + burned-in captions."""

import subprocess
from pathlib import Path

from ..config import Settings

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}


def list_visuals(folder: Path) -> list[Path]:
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS | VIDEO_EXTS)
    if not files:
        raise FileNotFoundError(f"No images or video clips found in {folder}")
    return files


def render(visuals: list[Path], narration: Path, captions_file: Path, duration: float,
           out_mp4: Path, settings: Settings) -> None:
    """Each visual gets an equal slice of the narration's length, cropped to fill 9:16."""
    w, h, fps = settings.width, settings.height, settings.fps
    slice_len = duration / len(visuals)

    cmd = [settings.ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    for v in visuals:
        if v.suffix.lower() in IMAGE_EXTS:
            cmd += ["-loop", "1", "-t", f"{slice_len:.3f}", "-i", str(v)]
        else:
            cmd += ["-stream_loop", "-1", "-t", f"{slice_len:.3f}", "-i", str(v)]
    cmd += ["-i", str(narration)]

    filters = []
    for i in range(len(visuals)):
        filters.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
            f"setsar=1,fps={fps},format=yuv420p,trim=duration={slice_len:.3f},setpts=PTS-STARTPTS[v{i}]"
        )
    joined = "".join(f"[v{i}]" for i in range(len(visuals)))
    filters.append(f"{joined}concat=n={len(visuals)}:v=1:a=0[vcat]")
    # The subtitles filter is given a bare filename (ffmpeg runs in that folder) to avoid
    # Windows drive-letter escaping problems.
    filters.append(f"[vcat]subtitles={captions_file.name}[vout]")

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", f"{len(visuals)}:a",
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(out_mp4.resolve()),
    ]
    result = subprocess.run(cmd, cwd=captions_file.parent, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed:\n{result.stderr.strip()}")
