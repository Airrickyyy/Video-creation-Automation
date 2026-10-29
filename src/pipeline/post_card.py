"""Post card: a forum-style post drawn over the background while the narrator reads.

Three modes (post.json "mode"):
    grow   (default) the post fills in word by word, the card growing downward, with each
           part's action bar (votes, comments) riding just below its newest line
    intro  the whole title is on screen from the first frame and disappears once it has been
           read; captions carry the rest (the "title card, then one-word captions" style)
    chat   a dialogue box: lines starting with "Name:" become messages with a bold speaker

The card is drawn with Pillow as one transparent PNG per reveal step, and an FFmpeg concat
list shows each PNG for exactly as long as it's current. The renderer overlays that on the
background. Text is laid out once with every word in place, so lines never reflow as words
appear. If the text runs past the card's maximum height, it continues on a fresh "page".

Three color themes: light (the default and the owner's preferred look), dark and blue;
"auto" picks one per video. Deliberately generic: a made-up community ("c/..."), no logos or exact UI of a real site.
"""

import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"

# Card geometry, in output pixels (the video is 1080 wide).
CARD_W = 920
PAD = 40
AVATAR = 60
NAME_SIZE = 30
TITLE_SIZE = 50
BODY_SIZE = 38
CHAT_SIZE = 48
LINE = 1.3  # line height as a multiple of font size
SECTION_GAP = 30
MESSAGE_GAP = 10  # extra space before each chat message
RADIUS = 28
SHADOW = 30  # transparent margin around the card for its shadow
BAR_GAP = 18  # space between a part's text and its action bar
BAR_H = 52

THEMES = {
    "light": {"card": (255, 255, 255), "ink": (26, 26, 27), "muted": (110, 114, 117),
              "pill": (234, 237, 239), "divider": (230, 231, 233), "speaker": (0, 121, 211)},
    "dark": {"card": (26, 27, 30), "ink": (236, 238, 240), "muted": (139, 145, 150),
             "pill": (52, 54, 58), "divider": (52, 54, 58), "speaker": (88, 190, 255)},
    "blue": {"card": (66, 139, 236), "ink": (255, 255, 255), "muted": (214, 230, 252),
             "pill": (92, 158, 242), "divider": (110, 168, 244), "speaker": (255, 226, 102)},
}
VOTE = (255, 69, 0)  # the up-arrow color
AVATAR_COLORS = [(255, 87, 34), (0, 150, 136), (63, 81, 181), (233, 30, 99), (121, 85, 72), (0, 121, 191)]
SPEAKER = re.compile(r"^[A-Z][\w'-]{0,19}:$")  # "Cashier:", "Me:", "Mom:"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for name in names:
        path = FONT_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size)


def seeded(text: str, low: int, high: int) -> int:
    """A stable pseudo-random number for this text, so re-renders look the same."""
    return low + int(hashlib.md5(text.encode()).hexdigest(), 16) % (high - low)


def short_count(n: int) -> str:
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def rgba(color: tuple) -> tuple:
    return color + (255,) if len(color) == 3 else color


def make_avatar(name: str, image: Path | None) -> Image.Image:
    """The given picture cropped to a circle, or a colored circle with the name's first letter."""
    if image and image.exists():
        src = Image.open(image).convert("RGBA")
        side = min(src.size)
        src = src.crop(((src.width - side) // 2, (src.height - side) // 2,
                        (src.width + side) // 2, (src.height + side) // 2)).resize((AVATAR, AVATAR))
    else:
        color = AVATAR_COLORS[seeded(name, 0, len(AVATAR_COLORS))]
        src = Image.new("RGBA", (AVATAR, AVATAR), color + (255,))
        draw = ImageDraw.Draw(src)
        draw.text((AVATAR / 2, AVATAR / 2), name[:1].upper(), font=load_font(30, bold=True),
                  fill=(255, 255, 255, 255), anchor="mm")
    mask = Image.new("L", (AVATAR, AVATAR), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, AVATAR - 1, AVATAR - 1), fill=255)
    out = Image.new("RGBA", (AVATAR, AVATAR), (0, 0, 0, 0))
    out.paste(src, (0, 0), mask)
    return out


@dataclass
class Section:
    """One part of the card: an optional header row, then text."""
    kind: str  # "post" (community header), "continue" / "chat" (no header), or "reply" (user header)
    name: str  # community for a post, username for a reply
    meta: str  # small grey text, e.g. "6h"
    avatar: Image.Image | None
    words: list[str]
    font: ImageFont.FreeTypeFont
    group: int = 0  # sections sharing a group share one action bar (a post and its continuation)
    byline: str = ""  # second header line for a post, e.g. "u/throwaway_kev88"
    bar: list[str] = field(default_factory=list)  # action bar labels; empty = no bar
    speakers: set[int] = field(default_factory=set)  # chat: indexes of "Name:" words that start a message
    first_word: int = 0  # index of this section's first word in the whole card


@dataclass
class Placed:
    kind: str  # "header" or "word"
    page: int
    y: int
    bottom: int
    section: int
    word: int = -1  # global word index for "word" items
    x: int = 0
    text: str = ""
    font: ImageFont.FreeTypeFont | None = None
    color: str = "ink"  # theme key


@dataclass
class Layout:
    items: list[Placed] = field(default_factory=list)
    word_page: list[int] = field(default_factory=list)


def layout_post(sections: list[Section], max_height: int) -> Layout:
    out = Layout()
    page, y, index = 0, PAD, 0
    text_w = CARD_W - 2 * PAD
    limit = max_height - PAD - BAR_GAP - BAR_H  # always leave room for the action bar

    def header(si: int) -> None:
        nonlocal y
        if sections[si].kind == "continue":
            y += 10  # breathing room between the bold title and the body
        if sections[si].kind in ("continue", "chat"):
            return
        out.items.append(Placed("header", page, y, y + AVATAR, si))
        y += AVATAR + 16

    for si, sec in enumerate(sections):
        sec.first_word = index
        if si > 0 and sec.group != sections[si - 1].group:
            y += BAR_GAP + BAR_H + SECTION_GAP  # the previous part's action bar sits here
        header(si)
        line_h = int(sec.font.size * LINE)
        bold = load_font(sec.font.size, bold=True)
        space = sec.font.getlength(" ")
        x = 0.0
        for local, word in enumerate(sec.words):
            is_speaker = local in sec.speakers
            font = bold if is_speaker else sec.font
            w = font.getlength(word)
            if is_speaker and local > 0:  # every message starts on its own line
                x, y = 0.0, y + line_h + MESSAGE_GAP
            elif x > 0 and x + w > text_w:  # wrap
                x, y = 0.0, y + line_h
            if y + line_h > limit:  # card full: continue on a new page
                page, y, x = page + 1, PAD, 0.0
                header(si)
            out.items.append(Placed("word", page, y, y + line_h, si, index, PAD + int(x), word, font,
                                    "speaker" if is_speaker else "ink"))
            out.word_page.append(page)
            x += w + space
            index += 1
        y += line_h
    return out


def draw_header(canvas: Image.Image, sec: Section, y: int, theme: dict) -> None:
    draw = ImageDraw.Draw(canvas)
    ink, muted = rgba(theme["ink"]), rgba(theme["muted"])
    if sec.avatar:
        canvas.alpha_composite(sec.avatar, (SHADOW + PAD, SHADOW + y))
    nx = SHADOW + PAD + AVATAR + 18
    bold, small = load_font(NAME_SIZE - 2, bold=True), load_font(NAME_SIZE - 6)
    if sec.kind == "post":  # two lines: community · time, then the poster
        draw.text((nx, SHADOW + y + 16), sec.name, font=bold, fill=ink, anchor="lm")
        draw.text((nx + bold.getlength(sec.name) + 10, SHADOW + y + 16), f"· {sec.meta}",
                  font=small, fill=muted, anchor="lm")
        draw.text((nx, SHADOW + y + 46), sec.byline, font=small, fill=muted, anchor="lm")
    else:
        mid = SHADOW + y + AVATAR // 2
        draw.text((nx, mid), sec.name, font=bold, fill=ink, anchor="lm")
        draw.text((nx + bold.getlength(sec.name) + 10, mid), f"· {sec.meta}", font=small, fill=muted, anchor="lm")


def draw_bar(canvas: Image.Image, labels: list[str], y: int, theme: dict) -> None:
    """Rounded pills: [▲ votes ▼]  [speech bubble + count]  [share arrow + Share]."""
    draw = ImageDraw.Draw(canvas)
    font = load_font(26, bold=True)
    ink, muted, pill = rgba(theme["ink"]), rgba(theme["muted"]), rgba(theme["pill"])
    x, top, bottom = SHADOW + PAD, SHADOW + y, SHADOW + y + BAR_H
    mid = (top + bottom) // 2
    for i, label in enumerate(labels):
        width = int(font.getlength(label)) + (128 if i == 0 else 92)
        draw.rounded_rectangle((x, top, x + width, bottom), BAR_H // 2, fill=pill)
        if i == 0:  # up arrow, count, down arrow
            draw.polygon([(x + 22, mid + 9), (x + 36, mid - 11), (x + 50, mid + 9)], fill=rgba(VOTE))
            draw.text((x + 62, mid), label, font=font, fill=ink, anchor="lm")
            ax = x + width - 50
            draw.polygon([(ax + 8, mid - 9), (ax + 22, mid + 11), (ax + 36, mid - 9)], fill=muted)
        elif i == 1:  # speech bubble
            draw.rounded_rectangle((x + 20, mid - 13, x + 50, mid + 9), 7, outline=muted, width=3)
            draw.polygon([(x + 26, mid + 8), (x + 26, mid + 17), (x + 35, mid + 8)], fill=muted)
            draw.text((x + 62, mid), label, font=font, fill=ink, anchor="lm")
        else:  # share: a bent arrow
            draw.line((x + 22, mid + 10, x + 22, mid, x + 46, mid), fill=muted, width=4)
            draw.polygon([(x + 42, mid - 9), (x + 54, mid), (x + 42, mid + 9)], fill=muted)
            draw.text((x + 64, mid), label, font=font, fill=ink, anchor="lm")
        x += width + 14


def draw_state(sections: list[Section], lay: Layout, revealed: int, max_height: int,
               theme: dict = THEMES["light"]) -> Image.Image:
    """The card with the first `revealed` words visible (0 = just the post's header, if any)."""
    canvas = Image.new("RGBA", (CARD_W + 2 * SHADOW, max_height + 2 * SHADOW), (0, 0, 0, 0))
    page = lay.word_page[revealed - 1] if revealed else 0
    shown = [it for it in lay.items if it.page == page and (
        (it.kind == "word" and it.word < revealed) or
        (it.kind == "header" and (sections[it.section].first_word < revealed or it.section == 0)))]
    if not shown:  # e.g. a chat box before its first word
        return canvas

    # Each part's action bar rides just below that part's newest visible line.
    bars: dict[int, int] = {}
    for it in shown:
        g = sections[it.section].group
        bars[g] = max(bars.get(g, 0), it.bottom + BAR_GAP)
    bars = {g: y for g, y in bars.items() if next(s.bar for s in sections if s.group == g)}
    height = max([it.bottom for it in shown] + [y + BAR_H for y in bars.values()]) + PAD

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (SHADOW, SHADOW + 6, SHADOW + CARD_W, SHADOW + height + 6), RADIUS, fill=(0, 0, 0, 90))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((SHADOW, SHADOW, SHADOW + CARD_W, SHADOW + height), RADIUS, fill=rgba(theme["card"]))

    for it in shown:
        if it.kind == "header":
            if sections[it.section].kind == "reply" and it.y > PAD:  # line between the post and a reply
                ly = SHADOW + it.y - SECTION_GAP // 2 - 4
                draw.line((SHADOW + PAD, ly, SHADOW + CARD_W - PAD, ly), fill=rgba(theme["divider"]), width=2)
            draw_header(canvas, sections[it.section], it.y, theme)
        else:
            draw.text((SHADOW + it.x, SHADOW + it.y), it.text, font=it.font, fill=rgba(theme[it.color]))
    for g, y in bars.items():
        draw_bar(canvas, next(s.bar for s in sections if s.group == g), y, theme)
    return canvas


def pick_theme(post: dict, seed: str) -> dict:
    name = post.get("theme", "light")
    if name == "auto":
        name = sorted(THEMES)[seeded(seed + "theme", 0, len(THEMES))]
    return THEMES[name]


def make_sections(post: dict, title: list[str], rest: list[str], input_dir: Path) -> list[Section]:
    """post.json fields (all optional except author, which chat mode doesn't need):
        mode            "grow" (default), "intro" or "chat" (see the module docstring)
        theme           "light" (default), "dark", "blue", or "auto" (picked per video)
        author          poster's username, shown as "u/<author>"
        community       made-up community name, shown as "c/<community>" (default "TrueStories")
        meta            post age, e.g. "6h"
        votes, comments numbers for the post's action bar (default: stable random)
        title_sentences how many opening sentences are the bold title (default 1)
        reply_author    if set, the rest of the script is this user's reply
        reply_meta, reply_votes
        avatar, reply_avatar   image files in the input folder for the profile pictures
    """
    def avatar(key: str, name: str) -> Image.Image:
        return make_avatar(name, input_dir / post[key] if post.get(key) else None)

    if post.get("mode") == "chat":
        words = title + rest
        speakers = {i for i, w in enumerate(words) if SPEAKER.match(w)}
        return [Section("chat", "", "", None, words, load_font(CHAT_SIZE), speakers=speakers)]

    author, community_name = post.get("author", "anonymous"), post.get("community", "TrueStories")
    community = f"c/{community_name}"
    seed = " ".join(title)
    votes = post.get("votes", seeded(seed, 2_000, 48_000))
    comments = post.get("comments", seeded(seed + "c", 150, 3_500))
    post_bar = [short_count(votes), short_count(comments), "Share"]

    sections = [Section("post", community, post.get("meta", "6h"), avatar("avatar", community_name), title,
                        load_font(TITLE_SIZE, bold=True), group=0, byline=f"u/{author}", bar=post_bar)]
    if post.get("mode") == "intro":
        return sections  # just the title; captions carry the rest
    if rest and post.get("reply_author"):
        reply = post["reply_author"]
        reply_votes = post.get("reply_votes", seeded(seed + "r", 500, max(votes, 600)))
        sections.append(Section("reply", reply, post.get("reply_meta", "5h"), avatar("reply_avatar", reply), rest,
                                load_font(BODY_SIZE), group=1, bar=[short_count(reply_votes), "Reply"]))
    elif rest:  # a story post: the body continues under the title
        sections.append(Section("continue", "", "", None, rest, load_font(BODY_SIZE), group=0, bar=post_bar))
    return sections


def build_card_track(post: dict, sentence_words: list[list[str]], word_starts: list[float],
                     duration: float, input_dir: Path, out_dir: Path, max_height: int) -> Path:
    """Render every reveal step and return an FFmpeg concat list that plays them in sync."""
    n_title = post.get("title_sentences", 1)
    title = [w for s in sentence_words[:n_title] for w in s]
    rest = [w for s in sentence_words[n_title:] for w in s]
    sections = make_sections(post, title, rest, input_dir)
    theme = pick_theme(post, " ".join(title))
    lay = layout_post(sections, max_height)
    out_dir.mkdir(parents=True, exist_ok=True)

    if post.get("mode") == "intro":
        # The full title from the first frame until it has been read, then nothing.
        full = out_dir / "card_title.png"
        draw_state(sections, lay, len(title), max_height, theme).save(full)
        empty = out_dir / "card_empty.png"
        Image.new("RGBA", (CARD_W + 2 * SHADOW, max_height + 2 * SHADOW), (0, 0, 0, 0)).save(empty)
        title_end = word_starts[len(title)] if rest else duration
        steps = [(full, title_end), (empty, duration - title_end)]
    else:
        total_words = sum(len(s.words) for s in sections)
        assert total_words == len(word_starts), (total_words, len(word_starts))
        times = [0.0] + word_starts  # state k is shown from times[k] (state 0 = before the first word)
        steps = []
        for k in range(total_words + 1):
            png = out_dir / f"card_{k:04d}.png"
            draw_state(sections, lay, k, max_height, theme).save(png)
            end = times[k + 1] if k < total_words else duration
            steps.append((png, end - times[k]))

    lines = ["ffconcat version 1.0"]
    for png, seconds in steps:
        lines += [f"file '{png.name}'", f"duration {max(seconds, 0.001):.3f}"]
    lines.append(f"file '{steps[-1][0].name}'")  # the concat demuxer needs the last file repeated
    track = out_dir / "cards.ffconcat"
    track.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return track
