# What makes a Short get views — research notes (Oct 2026)

Sources are mostly creator-tool blogs (vidIQ, Opus, quso, etc.). They agree on the *direction*
but their exact percentages conflict and rarely cite primary data, so treat numbers as rough
targets and compare against our own YouTube Studio analytics once videos are live.

## 1. How Shorts get distributed

- A new Short is shown to a small test audience. The first signal is **viewed vs. swiped away**
  (YouTube Studio → Analytics → Content → Shorts). If people stay, it's shown to more people;
  if they swipe, distribution tapers off.
- After that, **average percentage viewed** (retention) matters more than raw watch time,
  plus likes, shares, comments and "Not interested" clicks.
- Rough targets quoted: 70–90% "viewed" rather than swiped; keep most viewers past second 3.
- Since March 2025 replays count as views, so a Short that loops cleanly gets extra views.
  Only "engaged views" count toward monetization, though.

## 2. What the successful ones do

| Pattern | What it means for our scripts |
|---|---|
| **Hook in the first 1–3 seconds** | First sentence is the most surprising claim or image. No intro, no "did you know", no channel name. |
| **Open loop** | The hook raises a question the video answers only at the end, so viewers stay for the payoff. |
| **Short and dense** | Many sources put the sweet spot around 15–35s. Cut every sentence that doesn't move the story. Draft, then cut ~30%. |
| **Payoff, then loop** | End on the strongest line, ideally one that leads back into the first line so replays feel natural. |
| **Visual matches every line** | Change the picture every 3–5s, and show what the narrator is talking about. |
| **Big captions** | Most people watch muted at first; captions carry the hook. |
| **Story over list** | "Facts" channels that work tell one small story with stakes, not five unrelated facts. |

Niches repeatedly named for faceless Shorts: science/space facts, psychology and human behavior,
history and mysteries, true crime, personal finance (highest ad rates, highest scrutiny).

## 3. Policy: what to avoid

YouTube's July 2025 Partner Program update formalized that **"inauthentic" mass-produced,
repetitive content** can't be monetized. Using AI tools is explicitly allowed; churning out
near-identical template videos is not. For this project that means:

- each video needs a real story/angle and checked facts, not a fill-in-the-blank template;
- vary structure, visuals and topics; keep a human approval step (already in the plan);
- no reused clips from other creators; track sources and licenses (already in `sources.json`).

## Sources

- [vidIQ — How the YouTube Shorts algorithm works in 2026](https://vidiq.com/blog/post/youtube-shorts-algorithm/)
- [OutlierKit — Shorts algorithm in YouTube's words](https://outlierkit.com/resources/youtube-shorts-algorithm/)
- [Shortimize — Shorts retention rate](https://www.shortimize.com/blog/youtube-shorts-retention-rate)
- [Opus Clip — Ideal Shorts length & format for retention](https://www.opus.pro/blog/ideal-youtube-shorts-length-format-retention)
- [quso.ai — Video retention benchmarks](https://quso.ai/research/video-retention-benchmarks)
- [GoFaceless — High-retention Shorts attributes](https://www.gofaceless.ai/en/blog/high-retention-youtube-shorts-attributes)
- [aibrify — Shorts retention curve playbook](https://aibrify.com/en/blog/youtube-shorts-retention-curve-playbook)
- [Eliro — Faceless Shorts niches 2026](https://eliro.pro/blog/faceless-youtube-shorts-niches-2026)
- [Vozo — Faceless YouTube niches](https://www.vozo.ai/blogs/youtube/profitable-faceless-youtube-niches)
- [Social Media Today — YouTube clarifies inauthentic/repetitive content update](https://www.socialmediatoday.com/news/youtube-clarifies-monetization-update-inauthentic-repeated-content/752892/)
- [Gulf News — Inauthentic content rules take effect July 15](https://gulfnews.com/technology/youtube-updates-monetisation-policies-ai-and-repetitive-content-ban-begins-july-15-1.500192660)
