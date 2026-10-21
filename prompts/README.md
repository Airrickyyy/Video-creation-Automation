# Prompts for making a Short

Paste these into Claude chat (no API cost) in order. Replace the `{{...}}` parts.
They're built from the findings in [docs/RESEARCH.md](../docs/RESEARCH.md).

1. [01-ideas.md](01-ideas.md) — get 10 ranked video ideas for a niche
2. [02-script.md](02-script.md) — turn the best idea into a 15–35s narration script, with fact check
3. [03-visuals.md](03-visuals.md) — shot list + where to get each visual legally
4. [04-metadata.md](04-metadata.md) — title, description, hashtags

Then make the input folder and run the pipeline:

```
inputs/<video-name>/
├── script.txt      ← narration from step 2 (just the spoken words)
├── visuals/        ← files from step 3, named 01.jpg, 02.mp4, ... in script order
├── sources.json    ← where each visual came from + license
└── metadata.json   ← title/description/hashtags from step 4 (for later upload stages)
```

```
.\.venv\Scripts\python -m src.main inputs/<video-name>
```

`inputs/pale-blue-dot/` is a complete worked example made with these prompts.
