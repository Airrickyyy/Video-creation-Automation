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


def render(visuals: list[Path], slice_lens: list[float], narration: Path, captions_file: Path,
           duration: float, out_mp4: Path, settings: Settings) -> None:
    """Show each visual for its slice length, cropped to fill 9:16.

    Still images get a slow centered zoom (alternating in/out) so they don't sit frozen.
    """
    w, h, fps = settings.width, settings.height, settings.fps

    cmd = [settings.ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    for v, slice_len in zip(visuals, slice_lens):
        if v.suffix.lower() in IMAGE_EXTS:
            cmd += ["-i", str(v)]  # single frame; zoompan expands it to `frames`
        else:
            cmd += ["-stream_loop", "-1", "-t", f"{slice_len:.3f}", "-i", str(v)]
    cmd += ["-i", str(narration)]

    filters = []
    for i, (v, slice_len) in enumerate(zip(visuals, slice_lens)):
        frames = int(slice_len * fps) + 1
        if v.suffix.lower() in IMAGE_EXTS:
            # Zoom on a 2x canvas so the movement is smooth instead of stepping pixel by pixel.
            zoom = f"1+{settings.zoom}*on/{frames}" if i % 2 == 0 else f"{1 + settings.zoom}-{settings.zoom}*on/{frames}"
            frame = (
                f"scale={2 * w}:{2 * h}:force_original_aspect_ratio=increase,crop={2 * w}:{2 * h},"
                f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps}"
            )
        else:
            frame = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps}"
        filters.append(
            f"[{i}:v]{frame},setsar=1,format=yuv420p,"
            f"trim=duration={slice_len:.3f},setpts=PTS-STARTPTS[v{i}]"
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
