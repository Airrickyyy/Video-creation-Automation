"""Make one Short from an input folder.

    python -m src.main inputs/sample

The input folder needs:
    script.txt     narration text
    visuals/       images and/or video clips, used in filename order
    sources.json   (optional) where each visual came from and its license
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .config import ROOT, Settings
from .pipeline import captions, narration, render, validate


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


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
    segments = narration.synthesize(sentences, settings.piper_voice, work / "narration.wav", settings.sentence_gap)
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
    caps = captions.chunk_captions(segments, settings.words_per_caption)
    captions.write_ass(caps, work / "captions.ass", settings.width, settings.height,
                       settings.font, settings.font_size)

    print(f"  rendering {duration:.1f}s from {len(visuals)} visuals...")
    video = work / "video.mp4"
    render.render(visuals, slice_lens, work / "narration.wav", work / "captions.ass", duration, video, settings)

    print("  validating...")
    result = validate.validate(video, duration, settings)

    sources_file = input_dir / "sources.json"
    manifest = {
        "job_id": job_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "input": str(input_dir),
        "script": script_text,
        "duration": round(duration, 2),
        "render_sha256": sha256(video),
        "visuals": [{"file": v.name, "seconds": round(s, 2), "sha256": sha256(v)}
                    for v, s in zip(visuals, slice_lens)],
        "sources": json.loads(sources_file.read_text(encoding="utf-8")) if sources_file.exists() else None,
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
    return result["passed"], dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one vertical Short from a script and visuals.")
    parser.add_argument("input_dir", type=Path, help="folder with script.txt and visuals/")
    args = parser.parse_args()

    passed, dest = make_short(args.input_dir.resolve(), Settings.load())
    print(f"\n{'READY FOR REVIEW' if passed else 'FAILED VALIDATION'}: {dest / 'video.mp4'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
