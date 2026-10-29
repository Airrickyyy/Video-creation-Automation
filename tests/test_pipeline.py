"""Run with:  .venv\\Scripts\\python -m unittest discover tests -v"""

import json
import unittest
from pathlib import Path

from src.config import ROOT, Settings
from src.pipeline.captions import HIGHLIGHT, ass_text, ass_time, chunk_captions, mark_words
from src.pipeline.narration import Segment, split_sentences, split_shots


class TestText(unittest.TestCase):
    def test_split_sentences(self):
        self.assertEqual(
            split_sentences("One fact.  Two?\nThree!   "),
            ["One fact.", "Two?", "Three!"],
        )

    def test_split_shots_by_blank_lines(self):
        self.assertEqual(
            split_shots("First. Second.\n\n  \nThird!\n\n\n"),
            [["First.", "Second."], ["Third!"]],
        )

    def test_highlight_marks(self):
        self.assertEqual(
            mark_words("sold it for *forty dollars,* then *cried*. Done"),
            ["sold", "it", "for", "*forty*", "*dollars,*", "then", "*cried.*", "Done"],
        )
        self.assertEqual(ass_text("*HI*"), r"{\c" + HIGHLIGHT + r"}HI{\r}")

    def test_ass_time(self):
        self.assertEqual(ass_time(0), "0:00:00.00")
        self.assertEqual(ass_time(61.234), "0:01:01.23")
        self.assertEqual(ass_time(3600.5), "1:00:00.50")

    def test_captions_cover_each_sentence_in_order(self):
        segs = [Segment("one two three four five six", 0.0, 3.0), Segment("seven eight", 3.25, 4.0)]
        caps = chunk_captions(segs, words_per_caption=4)
        self.assertEqual([c.text for c in caps], ["one two three four", "five six", "seven eight"])
        self.assertEqual(caps[0].start, 0.0)
        self.assertEqual(caps[1].end, 3.0)
        self.assertEqual(caps[2].start, 3.25)
        for a, b in zip(caps, caps[1:]):
            self.assertLessEqual(a.end, b.start + 1e-9)


class TestPostCard(unittest.TestCase):
    def test_long_text_pages_instead_of_overflowing(self):
        from src.pipeline import post_card as pc

        sections = pc.make_sections({"author": "someone"}, ["A", "title."], ["word"] * 400, ROOT)
        lay = pc.layout_post(sections, max_height=600)
        self.assertEqual(len(lay.word_page), 402)
        self.assertGreater(max(lay.word_page), 0)
        # text never runs into the space reserved for the action bar
        self.assertTrue(all(it.bottom <= 600 - pc.PAD - pc.BAR_GAP - pc.BAR_H for it in lay.items))
        self.assertEqual(lay.word_page, sorted(lay.word_page))
        img = pc.draw_state(sections, lay, 402, 600)
        self.assertEqual(img.size, (pc.CARD_W + 2 * pc.SHADOW, 600 + 2 * pc.SHADOW))

    def test_counts(self):
        from src.pipeline.post_card import short_count

        self.assertEqual([short_count(n) for n in (950, 1000, 12_400, 3_050)], ["950", "1k", "12.4k", "3k"])


class TestEndToEnd(unittest.TestCase):
    """Renders the sample Short; needs FFmpeg and the Piper voice installed."""

    def test_sample_short_passes_validation(self):
        from src.main import make_short

        try:
            settings = Settings.load()
        except FileNotFoundError as e:
            self.skipTest(str(e))
        if not settings.piper_voice.exists():
            self.skipTest("Piper voice not downloaded")

        passed, dest = make_short(ROOT / "inputs" / "sample", settings)
        manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
        failed = {k: v for k, v in manifest["validation"]["checks"].items() if not v["ok"]}
        self.assertTrue(passed, f"failed checks: {failed}")
        self.assertEqual(dest.parent, ROOT / "output" / "review")
        self.assertTrue((dest / "video.mp4").exists())


if __name__ == "__main__":
    unittest.main()
