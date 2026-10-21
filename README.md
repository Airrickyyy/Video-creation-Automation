# YouTube Shorts Factory

Makes faceless vertical Shorts (1080×1920 MP4) from a script and a folder of visuals:
script → Piper narration → timed captions → FFmpeg render → automatic checks → review folder.

Everything runs locally and costs nothing. The full plan is in [docs/HANDOFF.md](docs/HANDOFF.md).
**Current stage: 1 of 6 (local proof of concept).** Nothing uploads anywhere.

## One-time setup (Windows)

```powershell
winget install Gyan.FFmpeg.Essentials          # then open a NEW terminal
py -3.14 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m piper.download_voices en_US-lessac-medium --data-dir voices
copy .env.example .env                          # optional, defaults work
```

Python 3.14 works with Piper 1.8. If a future Piper release drops it, use `py -3.12` instead.

## Make a Short

```powershell
.\.venv\Scripts\python -m src.main inputs/sample
```

The finished video lands in `output/review/<job-id>/video.mp4`, next to `script.txt`,
`captions.ass`, `narration.wav` and `manifest.json` (validation results, file hashes, sources).
If any check fails it goes to `output/failed/` instead and the command exits with code 1.

### Your own video

Make a folder like `inputs/sample`:

```
inputs/my-video/
├── script.txt      what the narrator says (end sentences with . ! or ?)
├── visuals/        images and/or clips, used in filename order (01.jpg, 02.mp4, ...)
└── sources.json    optional: where each visual came from and its license
```

**Matching visuals to lines:** separate `script.txt` into paragraphs with blank lines, one
paragraph per visual. If the paragraph count equals the number of visuals, each cut happens
exactly when its paragraph starts being spoken. Otherwise visuals get equal shares of the time.
Visuals are cropped to fill the vertical frame and still images slowly zoom.

Only use visuals you made yourself or have a license for (e.g. NASA, Pexels), and record them in `sources.json`.

**Writing a new video:** see [prompts/](prompts/README.md) for the Claude chat prompts (ideas →
script with fact check → visuals → title/description), based on [docs/RESEARCH.md](docs/RESEARCH.md).
`inputs/pale-blue-dot/` is a full worked example.

## Checks run on every video

File exists · H.264 video · exactly 1080×1920 · has audio · length matches narration ·
under `MAX_DURATION` · audio isn't silent · no black stretches ≥ 1s.

## Tests

```powershell
.\.venv\Scripts\python -m unittest discover tests -v
```

The end-to-end test renders the sample video (about 30 seconds).

## Known limitations (Stage 1)

- Image movement is a simple centered zoom; no pans or transitions between shots.
- No background music.
- Caption timing is per sentence, split evenly by characters, so words can be a little off.
- Scripts are written by hand (or with Claude in chat) and saved as `script.txt`.
- The sample visuals are plain gradients, placeholders only.
