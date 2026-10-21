"""Growing post card: a forum-style post that fills in word by word as the narrator reads it.

The post is drawn with Pillow as one transparent PNG per reveal step, and an FFmpeg concat
list shows each PNG for exactly as long as it's current. The renderer overlays that on the
background. Text is laid out once with every word in place, so lines never reflow as words
appear; the card simply grows downward. If the text runs past the card's maximum height,
it continues on a fresh "page" of the same card.

Deliberately generic: no logos, names or exact UI of any real site.
"""

import hashlib
import os
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
LINE = 1.3  # line height as a multiple of font size
SECTION_GAP = 30
RADIUS = 28
SHADOW = 30  # transparent margin around the card for its shadow

INK = (26, 26, 27, 255)
MUTED = (120, 124, 126, 255)
DIVIDER = (230, 231, 233, 255)
AVATAR_COLORS = [(255, 87, 34), (0, 150, 136), (63, 81, 181), (233, 30, 99), (121, 85, 72), (0, 121, 191)]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for name in names:
        path = FONT_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size)


def make_avatar(name: str, image: Path | None) -> Image.Image:
    """The given picture cropped to a circle, or a colored circle with the name's first letter."""
    if image and image.exists():
        src = Image.open(image).convert("RGBA")
        side = min(src.size)
        src = src.crop(((src.width - side) // 2, (src.height - side) // 2,
                        (src.width + side) // 2, (src.height + side) // 2)).resize((AVATAR, AVATAR))
    else:
        color = AVATAR_COLORS[int(hashlib.md5(name.encode()).hexdigest(), 16) % len(AVATAR_COLORS)]
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
    """One author's part of the post: a name row, then their text."""
    name: str
    meta: str  # small grey text after the name, e.g. "7h"
    avatar: Image.Image
    words: list[str]
    font: ImageFont.FreeTypeFont
    first_word: int = 0  # index of this section's first word in the whole post


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


@dataclass
class Layout:
    items: list[Placed] = field(default_factory=list)
    word_page: list[int] = field(default_factory=list)


def layout_post(sections: list[Section], max_height: int) -> Layout:
    out = Layout()
    page, y, index = 0, PAD, 0
    text_w = CARD_W - 2 * PAD

    def header(si: int) -> None:
        nonlocal y
        if not sections[si].name:  # untitled section: the text just continues
            return
        out.items.append(Placed("header", page, y, y + AVATAR, si))
        y += AVATAR + 16

    for si, sec in enumerate(sections):
        sec.first_word = index
        if si > 0:
            y += SECTION_GAP
        header(si)
        line_h = int(sec.font.size * LINE)
        space = sec.font.getlength(" ")
        x = 0.0
        for word in sec.words:
            w = sec.font.getlength(word)
            if x > 0 and x + w > text_w:  # wrap
                x, y = 0.0, y + line_h
            if y + line_h > max_height - PAD:  # card full: continue on a new page
                page, y, x = page + 1, PAD, 0.0
                header(si)
            out.items.append(Placed("word", page, y, y + line_h, si, index, PAD + int(x), word, sec.font))
            out.word_page.append(page)
            x += w + space
            index += 1
        y += line_h
    return out


def draw_state(sections: list[Section], lay: Layout, revealed: int, max_height: int) -> Image.Image:
    """The card with the first `revealed` words visible (0 = just the first name row)."""
    page = lay.word_page[revealed - 1] if revealed else 0
    shown = [it for it in lay.items if it.page == page and (
        (it.kind == "word" and it.word < revealed) or
        (it.kind == "header" and (sections[it.section].first_word < revealed or it.section == 0)))]
    height = max(it.bottom for it in shown) + PAD

    canvas = Image.new("RGBA", (CARD_W + 2 * SHADOW, max_height + 2 * SHADOW), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (SHADOW, SHADOW + 6, SHADOW + CARD_W, SHADOW + height + 6), RADIUS, fill=(0, 0, 0, 90))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((SHADOW, SHADOW, SHADOW + CARD_W, SHADOW + height), RADIUS, fill=(255, 255, 255, 255))

    name_font, meta_font = load_font(NAME_SIZE, bold=True), load_font(NAME_SIZE - 4)
    for it in shown:
        if it.kind == "header":
            sec = sections[it.section]
            if it.section > 0 and it.y > PAD:  # thin line between the post and a reply
                ly = SHADOW + it.y - SECTION_GAP // 2 - 8
                draw.line((SHADOW + PAD, ly, SHADOW + CARD_W - PAD, ly), fill=DIVIDER, width=2)
            canvas.alpha_composite(sec.avatar, (SHADOW + PAD, SHADOW + it.y))
            mid = SHADOW + it.y + AVATAR // 2
            nx = SHADOW + PAD + AVATAR + 18
            draw.text((nx, mid), sec.name, font=name_font, fill=INK, anchor="lm")
            if sec.meta:
                mx = nx + name_font.getlength(sec.name) + 12
                draw.text((mx, mid), f"· {sec.meta}", font=meta_font, fill=MUTED, anchor="lm")
        else:
            draw.text((SHADOW + it.x, SHADOW + it.y), it.text, font=it.font, fill=INK)
    return canvas


def build_card_track(post: dict, sentence_words: list[list[str]], word_starts: list[float],
                     duration: float, input_dir: Path, out_dir: Path, max_height: int) -> Path:
    """Render every reveal step and return an FFmpeg concat list that plays them in sync.

    post.json fields: author, title_sentences (how many opening sentences are the post's title),
    optional reply_author (the rest of the script is then a reply), optional meta / reply_meta,
    and optional avatar / reply_avatar image paths relative to the input folder.
    """
    n_title = post.get("title_sentences", 1)
    title = [w for s in sentence_words[:n_title] for w in s]
    rest = [w for s in sentence_words[n_title:] for w in s]

    def avatar(key: str, name: str) -> Image.Image:
        return make_avatar(name, input_dir / post[key] if post.get(key) else None)

    author = post["author"]
    sections = [Section(author, post.get("meta", "7h"), avatar("avatar", author), title, load_font(TITLE_SIZE, bold=True))]
    if rest and post.get("reply_author"):
        reply = post["reply_author"]
        sections.append(Section(reply, post.get("reply_meta", "5h"), avatar("reply_avatar", reply), rest, load_font(BODY_SIZE)))
    elif rest:  # a story post: the body continues under the title with no second name row
        sections.append(Section("", "", sections[0].avatar, rest, load_font(BODY_SIZE)))

    lay = layout_post(sections, max_height)
    total_words = sum(len(s.words) for s in sections)
    assert total_words == len(word_starts), (total_words, len(word_starts))

    out_dir.mkdir(parents=True, exist_ok=True)
    times = [0.0] + word_starts  # state k is shown from times[k] (state 0 = before the first word)
    lines = ["ffconcat version 1.0"]
    for k in range(total_words + 1):
        png = out_dir / f"card_{k:04d}.png"
        draw_state(sections, lay, k, max_height).save(png)
        end = times[k + 1] if k < total_words else duration
        lines += [f"file '{png.name}'", f"duration {max(end - times[k], 0.001):.3f}"]
    lines.append(f"file 'card_{total_words:04d}.png'")  # the concat demuxer needs the last file repeated
    track = out_dir / "cards.ffconcat"
    track.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return track
