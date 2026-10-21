# YouTube Shorts Factory — Project Handoff

**Purpose:** This document transfers the current planning discussion into Claude Code so implementation can continue without having to reconstruct the requirements from chat.

**Project status:** Planning / not yet implemented in this project. Treat the architecture and tool choices below as proposed defaults, not as completed work. Confirm the local machine, hardware, niche, and other open decisions before committing to costly or difficult-to-reverse choices.

---

## 1. Project vision

Build a mostly automated system that creates faceless, AI-assisted YouTube Shorts and queues finished videos for the owner's approval before publishing.

The owner wants to use tools already available:
- VS Code
- Claude Pro subscription, potentially with Claude Code
- Free online services and open-source software where practical

**Primary goals**
1. Minimize recurring cost, ideally $0 additional cost for the first prototype.
2. Minimize human interaction after initial setup.
3. Automate the pipeline from topic selection through rendered video.
4. Require explicit human approval before any upload or publication.
5. Keep the system modular so providers can be changed later.
6. Build and test incrementally rather than generating a huge, unverified codebase in one step.

**Important cost distinction:** Claude Pro provides access to Claude products according to its plan and usage limits. It should not be treated as unlimited API credits for an application. Claude API usage is billed separately. Avoid making the production application depend on Claude API calls unless the owner explicitly chooses that cost.

---

## 2. Desired end-to-end workflow

1. **Idea discovery**
   - Generate or collect topic candidates based on a configured niche.
   - Optionally use public trend/search sources or free APIs.
   - Rank ideas for interest, originality, clarity, suitability for Shorts, and ease of sourcing visuals.
   - Avoid copying other creators' scripts or reproducing copyrighted videos.

2. **Script generation**
   - Create a strong opening hook, concise narration, coherent story/explanation, and ending.
   - Save the script and its sources/research notes.
   - Where facts are involved, verify important claims against reliable sources and retain source URLs.
   - Flag uncertain claims rather than inventing facts.

3. **Narration**
   - Prefer a free, locally runnable text-to-speech option where quality and hardware allow.
   - Keep the TTS provider replaceable.
   - Do not clone a real person's voice without appropriate authorization.

4. **Visual sourcing**
   - Start with properly licensed stock footage and/or generated still images.
   - A Pexels API integration is a candidate, subject to API limits, licensing, and applicable attribution requirements.
   - Track the source, license, and download URL for each asset.
   - Do not assume arbitrary internet images, video clips, Reddit posts, or other creators' content can be reused.
   - Paid generative video is not required for the initial prototype. Highly customized AI-generated video may require paid services or substantial local computing.

5. **Video rendering**
   - Use FFmpeg to combine narration, visuals, captions, and appropriately licensed background audio.
   - Render vertical 9:16 MP4 suitable for Shorts.
   - Make timing, caption placement, font, transitions, music level, and duration configurable.
   - Check output files for valid duration, dimensions, audio, and subtitle timing before placing them in the approval queue.

6. **Quality checks**
   - Detect missing media, silent or broken audio, subtitle overflow, blank frames, render failures, and missing metadata.
   - Retry transient errors with a limit and useful logs.
   - Mark failed jobs clearly rather than silently passing them forward.

7. **Approval dashboard**
   - Show the rendered video preview, script, title, description, source notes, and status.
   - Support **Approve**, **Reject**, and **Regenerate** actions.
   - Permit edits to script/title/description before approval.
   - Approval must be explicit and tied to a particular video version.
   - If a video is regenerated or materially changed after approval, invalidate the previous approval.
   - Rejected videos must never enter the publishing queue.

8. **Publishing**
   - Integrate the official YouTube Data API only after local rendering and approval work reliably.
   - Require Google OAuth authorization and securely store credentials.
   - Upload and schedule only explicitly approved versions.
   - Start by testing private or unlisted uploads.
   - Store upload IDs, publication state, scheduled time, and errors.
   - Handle API quotas, restrictions, and upload failures.
   - Never auto-publish an unapproved video, even if a workflow retries or restarts.

9. **Feedback and improvement**
   - Later, optionally collect YouTube performance metrics such as views and audience retention where available.
   - Use performance data to inform future ideas, not to promise virality or automatically sacrifice originality.

---

## 3. Proposed technology stack

These are initial recommendations, not hard requirements.

### Development
- **VS Code** as the editor.
- **Claude Code** as the coding assistant, if available through the owner's Claude Pro plan and current usage limits.
- **Python** for orchestration, job management, API integrations, and automation.
- **Git** for version control and safe iteration.

### Rendering
- **FFmpeg** for local rendering. Verify installation and version.
- Python libraries only where they add value; avoid unnecessary dependencies.

### Storage
- Start with **SQLite** for local metadata and job state.
- Store video files and media assets on disk in a predictable project directory.
- Keep database records separate from large media files.
- Consider Supabase or another hosted database only if remote access or multi-device/cloud operation becomes necessary.

### User interface
- MVP can use a lightweight local web dashboard, such as Python with FastAPI and a simple frontend, or a small React UI if that is the owner's preference.
- Do not build a complex full-stack application before a single video can be rendered.
- The dashboard should run locally at first and not be exposed publicly without authentication and security review.

### Asset sourcing
- **Pexels API** is a candidate for free stock footage, subject to API limits and license terms.
- Other sources should be assessed individually. Maintain an asset provenance record.

### Text-to-speech and script generation
- Prefer a local TTS engine or a genuinely free online tier for the MVP.
- Use a provider adapter so the TTS engine can be changed.
- For scripts, begin with a pluggable interface. Options include manually initiated generation through Claude, a local model if hardware supports it, or an external API if the owner approves its cost.
- Do not assume the Claude Pro subscription includes application API credits.

### Automation scheduling
- Initially use a local Python scheduler/command runner or OS task scheduler.
- **n8n** is optional, not required. A local n8n instance can add workflow visibility, but introduces setup and maintenance. Do not pay for a hosted automation service unless needed.
- If the owner later wants production to run while the PC is off, assess a cloud worker and its recurring costs. Do not promise fully free, always-on execution without checking current service limits.

### Publishing
- Official **YouTube Data API** and Google OAuth.
- Verify current API policies, quota, upload restrictions, and account eligibility before implementation.

---

## 4. Cost and practical constraints

Target: **$0 in additional monthly spending for the first prototype**, where feasible.

Potentially free:
- VS Code, Python, Git, FFmpeg, SQLite
- Local dashboard and local scheduling
- Local TTS if the machine can run it
- Some stock footage through a free API tier
- Local file storage

Potential costs or limitations:
- Claude API is separate from Claude Pro.
- Hosted AI script generation, high-quality TTS, image generation, and generative video may cost money.
- Free APIs have quotas, terms, and availability limits.
- Local generation depends on CPU, RAM, GPU, and storage.
- Cloud hosting for always-on automation may incur fees.
- YouTube API uploads have quota and policy requirements.

Do not choose a paid service without explaining why it is necessary, the estimated usage/cost, and a free or lower-cost alternative. Check current provider pricing and terms before final recommendations.

---

## 5. MVP scope

Build in small, testable stages.

### Stage 1 — Local proof of concept
- Create the repository and Python environment.
- Add configuration via environment variables or a local config file.
- Generate or manually provide one script.
- Obtain one narration track.
- Source a small number of legally usable visuals.
- Render one complete vertical MP4 using FFmpeg.
- Validate dimensions, duration, audio, and caption timing.
- Document how to run the pipeline.

**Exit criterion:** A single complete Short can be generated reliably from a known input.

### Stage 2 — Repeatable pipeline
- Define a structured job record and statuses.
- Separate script, narration, media acquisition, rendering, and validation modules.
- Add retries, timeouts, logs, and failure reporting.
- Make output deterministic where possible.
- Ensure reruns do not duplicate jobs or corrupt prior outputs.

**Exit criterion:** Multiple videos can be generated without manual intervention between pipeline stages.

### Stage 3 — Approval dashboard
- List queued, generating, ready-for-review, approved, rejected, failed, and published jobs.
- Preview the MP4.
- Show and edit script and metadata.
- Implement approve, reject, and regenerate.
- Tie approval to an immutable video version/hash.
- Require explicit confirmation for any publishing action.

**Exit criterion:** A complete video can be reviewed and approved locally, and no unapproved video can be uploaded.

### Stage 4 — Batch automation
- Configure a target number of candidate videos per run/week.
- Automatically discover topics and process a batch.
- Add notifications when the approval queue is ready.
- Keep human work to reviewing, editing if needed, and approving/rejecting.
- Add rate limits and cost/usage safeguards.

**Exit criterion:** The pipeline can create a batch and wait safely for approval.

### Stage 5 — YouTube integration
- Configure Google Cloud project and YouTube Data API.
- Implement OAuth and secure token storage.
- Test private/unlisted uploads.
- Upload only approved video versions.
- Add scheduling, status tracking, and error recovery.
- Make the publishing gate auditable.

**Exit criterion:** Approved videos can be scheduled or uploaded without manual file transfer, while rejected/unapproved versions remain blocked.

### Stage 6 — Optional analytics and optimization
- Collect available performance metrics.
- Summarize which formats/topics appear to perform well.
- Use findings to inform idea ranking and templates.
- Keep content quality and policy compliance ahead of volume.

---

## 6. Approval and safety invariants

These requirements are non-negotiable:

- **No upload or publication without explicit approval.**
- Approval applies to a specific rendered version, not just the general idea.
- Any changed render or changed material content requires re-approval.
- Rejected, failed, and pending-review jobs cannot publish.
- Publishing must re-check approval immediately before upload.
- Use idempotency or equivalent duplicate prevention so retries do not cause duplicate uploads.
- Never store API keys, OAuth secrets, or passwords in source control.
- Keep secrets in environment variables or an appropriate local secret store; include `.env` in `.gitignore`.
- Keep an audit log of approvals, rejections, regeneration, and publishing.
- Make destructive actions reversible where possible.
- Respect licensing, privacy, platform terms, and YouTube monetization/content policies.
- Do not mass-produce repetitive, low-value videos. Add original narrative, meaningful editing, and editorial quality checks.
- Do not use deceptive synthetic media or impersonate people.
- Preserve sources for factual claims and assets.

---

## 7. Suggested folder structure

Start simple and adjust only when the implementation needs it.

```text
shorts-factory/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── config/
│   └── settings.example.yaml
├── data/
│   ├── shorts.db
│   ├── jobs/
│   └── media/
├── output/
│   ├── review/
│   ├── approved/
│   └── published/
├── logs/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── pipeline/
│   │   ├── ideas.py
│   │   ├── script.py
│   │   ├── narration.py
│   │   ├── assets.py
│   │   ├── captions.py
│   │   ├── render.py
│   │   └── validate.py
│   ├── providers/
│   │   ├── base.py
│   │   ├── stock.py
│   │   └── tts.py
│   ├── approval/
│   │   ├── queue.py
│   │   └── rules.py
│   └── publishing/
│       └── youtube.py
├── dashboard/
└── tests/
```

This is a suggested layout only. Avoid creating empty modules without a concrete use. Keep generated video files and secrets out of Git.

---

## 8. Initial data model

A `VideoJob` record should include, at minimum:

- `id`
- `status`
- `created_at`, `updated_at`
- `topic`
- `script`
- `research_sources`
- `title`, `description`, `tags`
- `asset_manifest` with URLs, source, and licensing/provenance details
- `voiceover_path`
- `render_path`
- `render_version` or file hash
- `validation_results`
- `approval_status`
- `approved_at`
- `approved_render_hash`
- `rejection_reason`
- `retry_count`, `last_error`
- `youtube_video_id`
- `scheduled_publish_at`
- `published_at`

Possible statuses:

`idea → scripting → sourcing_assets → generating_audio → rendering → validating → ready_for_review → approved → scheduled/publishing → published`

Failure/rejection statuses should be explicit. Transitions should be validated in code, not improvised by an LLM.

---

## 9. Decisions still open

Do not assume these have already been decided:

1. **Computer/runtime:** Windows PC, Mac, or cloud. If local, whether an NVIDIA GPU is available and the machine's RAM/storage.
2. **Niche:** Possible examples discussed include facts/mysteries/stories, history, Reddit-style narration, business/economics, or motivation. The owner has not selected one yet.
3. **Visual style:** AI-generated images/video, stock footage, or a mixture. A mixed approach is a practical MVP default.
4. **Weekly volume:** 1–2, 3–5, 7–14, or more. Not yet selected.
5. **TTS voice and language:** Not yet selected.
6. **Script generation method:** Local model, manual Claude-assisted generation, or paid/free external API. Must respect the separate Claude API billing model.
7. **Dashboard:** Lightweight local web UI versus React frontend.
8. **Publishing mode:** Manual publishing initially or automatic scheduled upload after approval. Either way, approval remains mandatory.
9. **Notifications:** Local dashboard, desktop notification, or email.
10. **Cloud/always-on operation:** Not required for the first prototype; revisit if the PC must be off.

Ask the owner for the **runtime machine and hardware first**, because it affects local AI feasibility and cost. Then choose a niche and video format before locking in providers.

---

## 10. First task for Claude Code

Do not try to implement the entire project immediately. Begin by confirming the development environment and delivering a minimal working vertical-video prototype.

### Instructions

1. Inspect the existing workspace before creating or overwriting files. If the folder is empty, initialize the project.
2. Ask for the OS and relevant hardware details if they are not known. Prefer Windows-compatible commands if the owner confirms Windows.
3. Recommend the cheapest practical local setup, clearly separating truly free components from free-tier or usage-limited online services.
4. Build only the smallest pipeline that:
   - accepts a script and a few local/licensed visual assets,
   - produces narration using the selected available method (or clearly identifies the missing TTS dependency),
   - creates captions,
   - renders a vertical MP4 using FFmpeg,
   - validates the output,
   - saves it into a local review folder.
5. Add a README with exact setup and run commands, a `.env.example` without secrets, and a `.gitignore`.
6. Include a test or validation script for the output file.
7. Do not add YouTube uploading until the rendering pipeline works and the approval gate has been implemented and tested.
8. Do not install unnecessary dependencies or require paid APIs for the first prototype.
9. Report files created, commands run, tests and results, known limitations, and the next single recommended step.
10. If information is missing, ask only the most important blocking question rather than making expensive assumptions.

### Definition of success for the first task

A command can generate one playable vertical MP4 with narration and captions from known inputs, using free/local components where feasible. It must be documented and reproducible. No upload capability is necessary at this stage.

---

## 11. What success looks like long term

After initial setup, the owner should ideally only need to:

1. Occasionally review the niche, template, and production settings.
2. Open the dashboard or notification when a batch is ready.
3. Watch each generated Short, make optional edits, and approve or reject it.
4. Let the system handle the remaining upload and scheduling work after approval.

The project should prioritize **reliability, low recurring cost, content quality, and safe approval-gated publishing** over the number of features in the first version.
