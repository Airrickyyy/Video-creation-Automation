# Research batch 2 — Minecraft/parkour Reddit-story Shorts (2026-10-22)

How this was gathered (yt-dlp, no logins):
1. 6 YouTube searches ("reddit stories minecraft parkour", "askreddit ...", "... horror", "... revenge",
   "... aita") → 249 unique videos, 59 of them Shorts.
2. 2 searches sorted by **view count** → the biggest videos in the niche.
3. The latest ~80 Shorts from 3 channels that clearly succeed at Shorts → hit vs. flop *within* a channel.
4. 9 Shorts studied closely: full script (auto-captions), speaking speed, frames every few seconds.

Views/likes as of 2026-10-22. Nothing here is reused; it's only studied.

---

## 1. The big picture

**Most videos in this niche get nothing.** Of 59 Shorts from plain searches, the **median had 1 view**.
One channel (alexuuu) has uploaded 30+ near-identical "r/AskReddit #askreddit #shorts" videos at
0–2 views each. Same background, same title, same structure → YouTube shows them to almost no one.
This is exactly the "generic / repetitive content" YouTube now suppresses.

**The money is concentrated in a few channels that do something specific:**

| Channel | Shorts studied | Median views | Best | What they do |
|---|---:|---:|---:|---|
| BrokenStories (548K subs) | 80 | **172,000** | 1.25M | Long (2.5–3 min) dramatic stories with a big premise |
| Amazing Stories (17K subs) | 80 | 37,000 | 1.05M | Very short funny/relatable posts with a punchline |
| (reddit memes channel) | 15 | 5,300 | 13,000 | Crude meme-style stories, slang titles |

**Surprise: the biggest view counts in the niche are long videos, not Shorts.** babyjamie1 gets
0.8–2.5M views per video with 25–60 minute "reddit stories and minecraft to fall asleep to /
study to" compilations, and several channels (Vembo, Droven, iReddit for Sleeping) copy it.
That's a second format worth considering later: our pipeline could stitch many stories into one.

---

## 2. Two formats that work (and one that "works" but we won't do)

### Format A — "Big premise drama" (BrokenStories: median 172K)
- **Title = the first sentence, word for word**, and it's a whole premise in one line:
  - "My grandfather's will said whoever lasted 72 hours alone in his cabin would inherit the property." (1.25M)
  - "They ranked us by face. We ranked them by character. Only one of those lists made people cry." (1.24M)
  - "My son's science project triggered a school lockdown. He built a radio." (922K)
- **A second hook within 5 seconds** that flashes forward: "The sheriff showed up with a search team on hour 26."
- **Specific numbers everywhere**: $600,000 property, 87 boys ranked, "I was 74".
- **Ends on justice or a satisfying twist**: "Turns out character does matter." / "Grandpa would have loved this episode."
- **Long for a Short: 150–179s, 680–920 words.**
- **Narration is fast: ~275–310 words per minute.** (Our Piper demo talks at ~200.)
- **Visual style:** dark tweet-style card with the title for the first ~2 seconds, then **one word at a time**,
  big, centered, alternating bright colors (yellow / green / pink), thick black outline.
  Background: Trackmania racing (not Minecraft), always moving.
- **Engagement is very high**: 4.5–5% of viewers like it (65K likes on 1.24M).

**Its flop (24K) is telling:** "My wife SKIPPED my mother's FUNERAL because her dog had a stomachache."
Same channel, same style, but it's a *cut from a long video* ("Watch the full video here") and it ends
mid-drama with **no payoff** ("The voicemail swung between sobbing and screaming."). No ending = no likes, no replays.

### Format B — "Short and funny" (Amazing Stories: median 37K, huge swings)
- Very short: **8s to 47s**. The 993K hit is **23 words, 8 seconds**:
  "Cashier: you're 8 cents short. Me: it's only 8 cents, can you let it slide? Cashier: no. Me: *slides cashier $20* what about now?"
- **Title is a reaction, not the story**: "The Cashier: 😐", "My BF's family is too smart 🧠", "This was so petty 💀"
- **One clear punchline**, relatable everyday situation (cashier, boyfriend's family, a date).
- **Visual style: a growing text box** near the top (sometimes blue with white text, sometimes dark
  "chat" style for dialogue). No separate captions. The box gets crowded on long ones, and still worked.
- It **varies its box style** between videos; probably helps it not look like a template.
- **Very hit-or-miss:** recent uploads range from **132 to 1M views**. Flops were jokes that need context
  ("Map people please 🙏", 164 views) or a famous old internet joke many people have already seen
  ("You can't take a girl to a book", 136 views).

### Format C — shock bait (we will NOT do this)
"I slept with my step brother..." (810K) and "My uncle is obsessed with my cat" (119K, innuendo throughout).
They get views, but:
- **like rates are terrible: 0.2–0.3%** (vs 4.5–5% for BrokenStories). People click and feel tricked.
- sexual / minors-adjacent content gets age-restricted, demonetized, or the channel struck.
- both are from 2024; that style isn't what's growing now.

---

## 3. Formatting checklist (what the good ones have in common)

| Element | What winners do |
|---|---|
| First frame | The hook text is **already on screen** at 0.0s (title card or first words). No intro. |
| Title | Format A: the first sentence. Format B: a short reaction + 1 emoji. **Never hashtags-only.** |
| Hashtags | 2–4 at the *end* of the description (#redditstory #redditstories). The 0-view channels stuff 8–10 into the title. |
| Captions | Either ONE word at a time, centered, colored (A) or a growing text box (B). |
| Speed | Fast. 270–310 wpm for drama. Pauses are cut. |
| Background | Constant motion, bright, high contrast. Minecraft parkour *or* Trackmania. Unrelated to the story. |
| Ending | A payoff line: verdict, twist, justice, or punchline. Never trailing off. |
| Length | Drama: 2.5–3 min if the story is strong. Jokes: under 30s. Middle-length rambling = weakest. |

---

## 4. What this means for our pipeline (proposed changes)

1. **Speed control for the voice.** Piper can talk faster (`length_scale`). Target ~270 wpm for drama.
2. **"One word at a time" caption mode** with alternating colors, centered, as an option next to our post card.
3. **Title-card intro option**: the hook shown as a post/tweet-style card for the first ~2s, then captions
   (BrokenStories style), instead of the card growing the whole time.
4. **Dialogue/chat card style** for "Cashier: / Me:" jokes (Format B).
5. **Vary the card style per video** (light/dark/colored) so the channel doesn't look templated.
6. Later: **long-form compilation mode** (stitch 10–20 stories into a 30–60 min video).

## 5. Content rules this confirms
- Original stories only. Several hits are clearly reposted famous posts/tweets; that's the reused-content
  risk, and the old famous ones performed *worse* anyway.
- Every story needs a real ending. Cut-off stories flop.
- No shock bait.
