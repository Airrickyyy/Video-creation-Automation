# 04 — Title, description, hashtags

```
Here is the final narration of a YouTube Short:

{{SCRIPT}}

Write:
1. 5 title options, each under 60 characters. They should create curiosity without
   lying or misleading (the video must deliver what the title promises). Mark your pick.
2. A description: 1–2 sentences that add one extra true detail, then a "Sources:" line with
   the fact-check links, then a "Credits:" line for every visual (from sources.json:
   {{SOURCES}}). Mention that the narration voice is AI-generated.
3. 3–5 hashtags, including #Shorts. Specific beats generic.

Return it as JSON: {"title": ..., "title_options": [...], "description": ..., "hashtags": [...]}
```

Save the JSON as `metadata.json` in the video's input folder.
