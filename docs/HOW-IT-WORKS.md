# How the Shorts Factory works

A beginner-friendly guide to everything in this project: what each tool is, what happens
when you make a video, what every file does, and how to change things yourself.

---

## 1. The big picture

This project turns **a text file** into **a finished vertical video**, entirely on your laptop.

```
 you write                      the program does                         you get
┌────────────┐   ┌───────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐
│ script.txt │──▶│ 1. Voice  │──▶│ 2. Text  │──▶│ 3. Video │──▶│ 4. Check │──▶│  video.mp4  │
│ visuals/   │   │  (Piper)  │   │ captions │   │ (FFmpeg) │   │ 8 tests  │   │ in output/  │
│ post.json  │   └───────────┘   │ + card   │   └──────────┘   └──────────┘   └─────────────┘
└────────────┘                   └──────────┘
```

Nothing is uploaded, and no paid service is used. There is no AI inside the program itself:
the scripts are written by a person (or by Claude in chat), and the program just *assembles*
them into a video the same way every time.

---

## 2. The tools, and why each one is here

| Tool | What it is | Why we use it |
|---|---|---|
| **Python** | A programming language | Glues every step together. All our code is Python. |
| **Virtual environment (`.venv`)** | A private folder of Python packages just for this project | So the packages we install can't break other projects on your PC. |
| **Piper** | Free text-to-speech that runs offline | Makes the narrator's voice. |
| **FFmpeg** | The standard free tool for editing video and audio from the command line | Crops, zooms, combines, burns in captions, and saves the MP4. |
| **Pillow** | A Python library for drawing images | Draws the white post card, one picture per word. |
| **yt-dlp** | A YouTube downloader | Only used to *study* reference Shorts, never inside our videos. |
| **Git + GitHub** | Version history + an online backup | Every "commit" is a snapshot you can go back to. |

### How to run Python from the project
Always use the project's own Python, which lives inside `.venv`:

```powershell
.\.venv\Scripts\python -m src.main inputs/demo-story
```

- `.\.venv\Scripts\python` = "use this project's Python"
- `-m src.main` = "run the file `src/main.py` as a module"
- `inputs/demo-story` = the folder with the video's ingredients

---

## 3. What you put in: the input folder

Each video has its own folder inside `inputs/`. Only the first two items are required.

```
inputs/demo-story/
├── script.txt      REQUIRED  what the narrator says
├── visuals/        REQUIRED  images and/or video clips (01.jpg, 02.mp4, ...)
├── post.json       optional  show the script as a growing post card
├── settings.json   optional  change the look for just this video
├── card.txt        optional  a simple title box at the top during the first sentence
├── sources.json    optional  where each visual came from + its license
├── metadata.json   optional  title / description / hashtags for uploading later
└── research.md     optional  your notes and fact checks
```

### `script.txt` — the narration
Plain text. A few special rules:

| You write | What happens |
|---|---|
| Sentences ending in `.` `!` or `?` | Each sentence is spoken separately, so we know exactly when it's said. |
| A **blank line** between paragraphs | If the number of paragraphs equals the number of visuals, each visual starts exactly when its paragraph starts. |
| `*forty dollars*` | Those words show in **yellow** in the captions. The asterisks are not spoken. |
| Numbers as words ("forty", not "40") | Makes the voice say them naturally. |

### `visuals/` — what's on screen
- Files are used in **name order**: `01.jpg`, `02.jpg`, ...
- **Images** are cropped to fill a phone screen and slowly zoom in or out.
- **Video clips** are cropped the same way and looped if they're too short. Their own sound is dropped.
- One long gameplay clip = a constant moving background for the whole video.

### `post.json` — the drop-down post card
```json
{"author": "throwaway_kev88", "meta": "6h", "title_sentences": 1}
```
| Field | Meaning |
|---|---|
| `author` | Username shown on the post |
| `meta` | Small grey text after the name, like "6h" |
| `title_sentences` | How many opening sentences are the **bold title** |
| `reply_author` | *(optional)* The rest becomes a **reply** from this user (question-and-answer style) |
| `avatar`, `reply_avatar` | *(optional)* Image file names for profile pictures; otherwise a colored letter circle |

### `settings.json` — per-video style
Anything in the settings list (section 6) can be changed for one video:
```json
{"words_per_caption": 3, "font_size": 76, "caption_align": 2, "caption_margin_v": 230}
```

### `sources.json` — where visuals came from
```json
{"01.mp4": {"url": "...", "credit": "...", "license": "...", "do_not_publish": true}}
```
`"do_not_publish": true` marks the whole video as **never publishable** (used for the demo's
borrowed gameplay). Always fill this in: it's your proof you're allowed to use each visual.

---

## 4. What happens when you run it, step by step

All of this is coordinated by **`src/main.py`**.

### Step 0 — Setup
- Loads settings (`src/config.py`), then applies the folder's `settings.json` on top.
- Makes a work folder: `data/jobs/<video-name>-<date-time>/`.

### Step 1 — The voice (`src/pipeline/narration.py`)
1. Splits the script into paragraphs, then sentences.
2. Feeds **one sentence at a time** to Piper, which returns raw audio.
3. Measures each sentence's length, e.g. *sentence 3 = 8.20s → 11.70s*.
4. Adds a 0.25s pause between sentences and saves everything as `narration.wav`.

Doing it sentence by sentence is the trick that makes everything else possible: we know
exactly when every sentence is spoken, without any speech recognition.

### Step 2 — Captions (`src/pipeline/captions.py`)
1. Splits each sentence into small chunks (e.g. 3 words).
2. Gives each chunk a share of its sentence's time, based on how many letters it has.
   (This is an *estimate*, which is why a word can be a hair early or late.)
3. Writes `captions.ass`, a subtitle file that also stores the **style**: font, size,
   black outline, position, and yellow for `*marked*` words.

> **What's an `.ass` file?** "Advanced SubStation Alpha", a subtitle format that supports
> fonts, colors and positions. FFmpeg can draw it straight onto the video.

### Step 3 — The post card (`src/pipeline/post_card.py`) — only if `post.json` exists
1. Lays out the **whole** post once (title, body, every word's exact position), so lines
   never jump around as words appear.
2. Draws one transparent PNG picture per word: picture 1 shows 1 word, picture 2 shows
   2 words, and so on. The white box is only as tall as the text so far, which is what
   makes it "drop down".
3. If the text gets too tall for the screen, it continues on a fresh page of the card.
4. Writes `card/cards.ffconcat`, a playlist that says "show picture 12 for 0.31 seconds,
   then picture 13 for 0.27 seconds...", timed to the voice.

### Step 4 — Render (`src/pipeline/render.py`)
Builds one long FFmpeg command and runs it. In plain words, that command says:

1. Take each visual → resize and **crop to 1080×1920** (vertical).
2. Still images → apply a slow **zoom**. Clips → **loop** them to the right length.
3. Join the visuals end to end.
4. Lay the **post card** playlist on top.
5. Draw the **captions** on top of that.
6. Add the **narration** as the soundtrack.
7. Save as an H.264 MP4 (the format every phone and YouTube plays).

### Step 5 — Checks (`src/pipeline/validate.py`)
Inspects the finished file with FFmpeg's tools:

| Check | Catches |
|---|---|
| file exists | render crashed |
| video stream is H.264 | wrong format |
| dimensions are 1080×1920 | not vertical |
| audio stream exists | silent export |
| duration matches narration | cut off or padded |
| under `MAX_DURATION` | too long for a Short |
| audio isn't silent | voice failed |
| no black stretches ≥ 1s | missing visuals |

### Step 6 — Sort and record
- **All checks pass** → copied to `output/review/<job>/`
- **Any check fails** → copied to `output/failed/<job>/`, and the command reports failure

Next to every video it saves `manifest.json`: the script, timings, sources, every check's
result, whether it's publishable, and a **fingerprint** (SHA-256 hash) of the video file.
The fingerprint will matter later: an approval will be tied to that exact file, so if the
video changes, it has to be approved again.

---

## 5. Every file in the project

```
Video-creation-Automation/
├── src/                    the program
│   ├── main.py             runs all the steps in order; writes manifest.json
│   ├── config.py           default settings; finds FFmpeg; reads .env
│   └── pipeline/
│       ├── narration.py    script → sentences → voice (Piper) → narration.wav
│       ├── captions.py     word chunks, highlight colors, title card → captions.ass
│       ├── post_card.py    draws the growing post card, one PNG per word
│       ├── render.py       builds and runs the FFmpeg command → video.mp4
│       └── validate.py     the 8 checks
├── tests/test_pipeline.py  automatic tests (run them after any change)
├── inputs/                 one folder per video (sample, pale-blue-dot, demo-story)
├── prompts/                prompts to paste into Claude chat to write new videos
├── library/                breakdowns of reference Shorts we studied
├── PLAYBOOK.md             the rules we've learned about what gets views
├── docs/
│   ├── HANDOFF.md          the original project plan (6 stages)
│   ├── RESEARCH.md         research on how Shorts get distributed
│   └── HOW-IT-WORKS.md     this file
├── requirements.txt        Python packages to install
├── .env.example            copy to .env to change settings for every video
└── .gitignore              files git must never upload

Not in git (too big, or re-downloadable — they only live on your PC):
├── .venv/                  the project's private Python + packages
├── voices/                 the Piper voice model (~60 MB)
├── backgrounds/            gameplay recordings
├── data/jobs/              work folders for every run
└── output/                 finished videos (review/ and failed/)
```

---

## 6. Settings you can change

Set them in `.env` (every video) or a folder's `settings.json` (one video).
`.env` uses UPPER_CASE names; `settings.json` uses the lower_case names.

| `settings.json` name | `.env` name | Default | What it does |
|---|---|---|---|
| `max_duration` | `MAX_DURATION` | 60 | Longest allowed video, in seconds |
| `font` | `CAPTION_FONT` | Arial | Caption font |
| `font_size` | `CAPTION_FONT_SIZE` | 84 | Caption size |
| `words_per_caption` | `WORDS_PER_CAPTION` | 4 | Words shown at a time |
| `zoom` | `IMAGE_ZOOM` | 0.12 | How far still images zoom (0 = none) |
| `caption_align` | — | 2 | 2 = bottom, 5 = middle of screen |
| `caption_margin_v` | — | 0 | Distance of bottom captions from the bottom edge (0 = a third of the way up) |
| `card_top` | — | 380 | Where the post card starts, from the top |
| `card_max_height` | — | 1100 | How tall the card grows before starting a new page |
| `sentence_gap` | — | 0.25 | Pause between sentences, in seconds |

---

## 7. Making a new video, start to finish

1. **Get an idea and script.** Open `prompts/README.md` and paste the prompts into Claude chat:
   ideas → script (with fact check) → visuals → title/description.
2. **Make the folder**: copy `inputs/demo-story` to `inputs/my-video`.
3. **Edit the files**: put the script in `script.txt`, mark key words with `*asterisks*`,
   set the username in `post.json`, and put your gameplay in `visuals/01.mp4`.
4. **Fill in `sources.json`** with where the gameplay came from (your own recording = easy).
5. **Run it**:
   ```powershell
   .\.venv\Scripts\python -m src.main inputs/my-video
   ```
6. **Watch it** in `output/review/my-video-<date-time>/video.mp4`.
7. Not happy? Change the script or settings and run it again. Each run makes a new folder,
   so old versions are never overwritten.

---

## 8. The research side (how the videos get *better*)

The code makes videos; these files decide **what** to make:

- **`docs/RESEARCH.md`**: how YouTube decides who sees a Short (the first 3 seconds and
  "viewed vs. swiped away" matter most), plus the policy rules to stay monetizable.
- **`library/`**: one file per batch of reference Shorts, with views, scripts and what
  separated hits from flops.
- **`PLAYBOOK.md`**: the rules we've learned, each with its evidence. The prompts follow it.

The learning loop:
```
study hits → write rules in PLAYBOOK → make videos → publish → read YouTube Studio numbers
     ▲                                                                  │
     └──────────────────── update the PLAYBOOK ◀────────────────────────┘
```
Other people's videos get you started; **your own numbers** are what make it good.

---

## 9. Rules this project never breaks

1. **Nothing gets uploaded without your approval** of that exact video file.
2. **Only footage you made or have a license for**, logged in `sources.json`.
3. **Original writing**: never read someone else's post word for word.
4. **No copying a real site's logo or interface** (the post card is deliberately generic).
5. **Secrets** (API keys, passwords) go in `.env`, which git never uploads.

---

## 10. Common problems

| Problem | Fix |
|---|---|
| `ffmpeg not found` | Open a **new** terminal (old ones don't see newly installed programs), or set `FFMPEG_DIR` in `.env`. |
| `Piper voice not found` | `.\.venv\Scripts\python -m piper.download_voices en_US-lessac-medium --data-dir voices` |
| `No module named ...` | `.\.venv\Scripts\python -m pip install -r requirements.txt` |
| `No images or video clips found` | The input folder needs a `visuals/` folder with at least one file. |
| Video landed in `output/failed/` | Read the `FAIL` lines it printed, or `validation` in that folder's `manifest.json`. |
| Captions slightly off from the voice | Expected: word timing is estimated (see Step 2). |

---

## 11. Git in 60 seconds

| Word | Meaning |
|---|---|
| **commit** | Save a snapshot of the project with a message, on your PC |
| **push** | Upload your commits to GitHub (your online backup) |
| **pull** | Download commits from GitHub (e.g. on another computer) |
| **.gitignore** | List of files git should never track |

Useful commands:
```powershell
git status          # what changed since the last commit
git log --oneline   # list of snapshots
```

---

## 12. Try these to learn

Each one teaches a different part. Re-run the demo after each change and watch what moves.

1. **Captions:** in `inputs/demo-story/settings.json`, change `"words_per_caption"` to `1`.
2. **Highlights:** add `*asterisks*` around a different word in `script.txt`.
3. **Post card:** in `post.json`, set `"title_sentences": 2`.
4. **Q&A style:** add `"reply_author": "quiet_maple"` to `post.json`.
5. **Card position:** add `"card_top": 250` to `settings.json`.
6. **Read code:** open `src/pipeline/captions.py` and find the line that sets the
   highlight color (`HIGHLIGHT = ...`). Colors are written blue-green-red, backwards from usual.
7. **Run the tests** after changes: `.\.venv\Scripts\python -m unittest discover tests`

---

## 13. What's built and what's next

| Stage (from `docs/HANDOFF.md`) | Status |
|---|---|
| 1. Make one video from a script | ✅ Done (plus post cards, captions, zoom) |
| 2. Repeatable pipeline with job tracking | ⬜ Next |
| 3. Approval dashboard (watch / approve / reject) | ⬜ |
| 4. Automatic batches | ⬜ |
| 5. YouTube uploading (only approved videos) | ⬜ |
| 6. Learn from your channel's analytics | ⬜ |

Open decisions: your own gameplay recording, ElevenLabs vs. Piper for the voice, and
pictures that pop in during stories.
