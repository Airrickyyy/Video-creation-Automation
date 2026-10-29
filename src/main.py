"""Make one Short from an input folder.

    python -m src.main inputs/sample

The input folder needs:
    script.txt     narration text
    visuals/       images and/or video clips, used in filename order
    sources.json   (optional) where each visual came from and its license;
                   a visual with "do_not_publish": true marks the video as not publishable
    card.txt       (optional) title card shown near the top while the first sentence is read
    post.json      (optional) show the script as a forum-style post that fills in as it's read;
                   see src/pipeline/post_card.py for the fields
    settings.json  (optional) per-video overrides of Settings fields, e.g. {"font_size": 110}
"""

import argparse
import dataclasses
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .config import ROOT, Settings
from .pipeline import captions, narration, post_card, render, validate


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def find_music(setting: str, input_dir: Path, seed: str) -> Path | None:
    """The background track: "" = none, "random" = one from music/, else a file path."""
    if not setting:
        return None
    if setting == "random":
        tracks = sorted(p for p in (ROOT / "music").glob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg"})
        if not tracks:
            raise FileNotFoundError("music is set to \"random\" but the music/ folder has no tracks")
        return tracks[int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(tracks)]
    for base in (input_dir, ROOT):
        if (base / setting).exists():
            return base / setting
    raise FileNotFoundError(f"Music file not found: {setting}")


def make_short(input_dir: Path, settings: Settings) -> tuple[bool, Path]:
    script_text = (input_dir / "script.txt").read_text(encoding="utf-8")
    visuals = render.list_visuals(input_dir / "visuals")

    job_id = f"{input_dir.name}-{datetime.now():%Y%m%d-%H%M%S}"
    work = ROOT / "data" / "jobs" / job_id
    work.mkdir(parents=True)
    print(f"[{job_id}] working in {work}")

    print("  narration...")
    shots = narration.split_shots(script_text)
    sentences = [s for shot in shots for s in shot]
    segments = narration.synthesize(sentences, work / "narration.wav", settings.sentence_gap,
                                    settings.speech_speed, settings.voice_engine, settings.piper_voice,
                                    settings.kokoro_model, settings.kokoro_voice)
    duration = segments[-1].end + settings.sentence_gap

    if len(shots) == len(visuals):
        # One paragraph per visual: cut exactly where each paragraph starts being spoken.
        starts, i = [], 0
        for shot in shots:
            starts.append(segments[i].start)
            i += len(shot)
        slice_lens = [b - a for a, b in zip(starts, starts[1:] + [duration])]
    else:
        slice_lens = [duration / len(visuals)] * len(visuals)

    print("  captions...")
    caps = captions.chunk_captions(segments, settings.words_per_caption) if settings.show_captions else []
    card_file = input_dir / "card.txt"
    card = card_file.read_text(encoding="utf-8").strip() if card_file.exists() else None
    captions.write_ass(caps, work / "captions.ass", settings.width, settings.height,
                       settings.font, settings.font_size, settings.caption_align,
                       card=card, card_end=segments[0].end, margin_v=settings.caption_margin_v,
                       cycle_colors=settings.caption_colors)

    overlay = None
    post_file = input_dir / "post.json"
    if post_file.exists():
        print("  post card...")
        words = captions.chunk_captions(segments, 1)  # one caption per word = each word's start time
        sentence_words = [[w.replace("*", "") for w in s.text.split()] for s in segments]
        sentence_words = [[w for w in s if w] for s in sentence_words]
        track = post_card.build_card_track(
            json.loads(post_file.read_text(encoding="utf-8")), sentence_words,
            [w.start for w in words], duration, input_dir, work / "card", settings.card_max_height)
        overlay = (track, (settings.width - post_card.CARD_W) // 2 - post_card.SHADOW,
                   settings.card_top - post_card.SHADOW)

    music = find_music(settings.music, input_dir, job_id)
    if music:
        print(f"  music: {music.name}")

    print(f"  rendering {duration:.1f}s from {len(visuals)} visuals...")
    video = work / "video.mp4"
    render.render(visuals, slice_lens, work / "narration.wav", work / "captions.ass", duration, video, settings,
                  overlay=overlay, music=music)

    print("  validating...")
    result = validate.validate(video, duration, settings)

    sources_file = input_dir / "sources.json"
    sources = json.loads(sources_file.read_text(encoding="utf-8")) if sources_file.exists() else None
    # A source marked "do_not_publish" (e.g. footage with an unverified license) blocks the
    # whole video from ever being published, even after approval.
    blocked = [name for name, s in (sources or {}).items() if s.get("do_not_publish")]
    manifest = {
        "job_id": job_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input": str(input_dir),
        "script": script_text,
        "duration": round(duration, 2),
        "render_sha256": sha256(video),
        "visuals": [{"file": v.name, "seconds": round(s, 2), "sha256": sha256(v)}
                    for v, s in zip(visuals, slice_lens)],
        "music": str(music.relative_to(ROOT)) if music and music.is_relative_to(ROOT) else (str(music) if music else None),
        "sources": sources,
        "publishable": not blocked,
        "segments": [vars(s) for s in segments],
        "validation": result,
    }
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    shutil.copy(input_dir / "script.txt", work / "script.txt")

    # Only videos that pass every check reach the review queue.
    dest = ROOT / "output" / ("review" if result["passed"] else "failed") / job_id
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(work, dest)

    for name, c in result["checks"].items():
        print(f"    {'PASS' if c['ok'] else 'FAIL'}  {name}: {c['detail']}")
    if blocked:
        print(f"  WARNING: not publishable, sources marked do_not_publish: {', '.join(blocked)}")
    return result["passed"], dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one vertical Short from a script and visuals.")
    parser.add_argument("input_dir", type=Path, help="folder with script.txt and visuals/")
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    settings = Settings.load()
    overrides = input_dir / "settings.json"
    if overrides.exists():
        settings = dataclasses.replace(settings, **json.loads(overrides.read_text(encoding="utf-8")))
    passed, dest = make_short(input_dir, settings)
    print(f"\n{'READY FOR REVIEW' if passed else 'FAILED VALIDATION'}: {dest / 'video.mp4'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
